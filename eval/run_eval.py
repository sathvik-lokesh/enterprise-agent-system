"""Text-to-SQL accuracy eval for the Data Analyst agent.

For each natural-language question we hold a *gold SQL* query whose result is
the ground truth. The ground truth is computed live from the same PostgreSQL
database the agent queries (the seed is deterministic, random.seed(42)), so the
numbers are never hardcoded and stay correct if the data is reseeded.

Two metrics are reported per case:

* execution accuracy (headline) — did any SQL the agent actually executed
  return the gold value? This is the standard text-to-SQL metric (cf. Spider).
  We capture the agent's own executed queries by teeing `run_query`; it
  isolates "did it write correct SQL" from the 3B model's narration quality.
* answer match (secondary) — did the gold value also survive into the agent's
  final natural-language answer?

Matching tolerates thousands separators, currency symbols and rounding
(138833.33 vs "138,833.33" vs "138,833") via a 1% / 0.5 tolerance.

Run:  .venv/bin/python eval/run_eval.py            # full run, writes RESULTS.md
      .venv/bin/python eval/run_eval.py --limit 3  # quick smoke test
"""

import argparse
import asyncio
import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.system import build_agents
from db.database import run_query  # unpatched: used only for gold ground truth

# --- capture the agent's own executed SQL results -------------------------
# tools.finance_tools holds its own reference to run_query; we wrap *that* one
# so the gold computation above (which imports run_query directly) is never
# captured. Capturing is gated by _CAPTURING so only the agent's turn counts.
import tools.finance_tools as ft

_CAPTURED: list[float] = []
_CAPTURING = False
_orig_run_query = ft.run_query


def _capturing_run_query(sql: str):
    rows = _orig_run_query(sql)
    if _CAPTURING:
        for row in rows:
            for val in row.values():
                # NUMERIC columns (salary/budget/amount) come back as Decimal;
                # COUNT(*) as int. Capture any non-bool number-like value.
                if isinstance(val, bool):
                    continue
                try:
                    _CAPTURED.append(float(val))
                except (TypeError, ValueError):
                    pass
    return rows


ft.run_query = _capturing_run_query

# (id, natural-language question, gold SQL returning a single scalar)
CASES = [
    ("total_headcount",
     "How many employees does the company have in total?",
     "SELECT count(*) FROM employees"),
    ("dept_count",
     "How many departments are there?",
     "SELECT count(*) FROM departments"),
    ("avg_salary_engineering",
     "What is the average salary in the Engineering department?",
     "SELECT avg(e.salary) FROM employees e JOIN departments d ON d.id = e.department_id "
     "WHERE d.name = 'Engineering'"),
    ("max_salary",
     "What is the highest salary in the company?",
     "SELECT max(salary) FROM employees"),
    ("min_salary_sales",
     "What is the lowest salary in the Sales department?",
     "SELECT min(e.salary) FROM employees e JOIN departments d ON d.id = e.department_id "
     "WHERE d.name = 'Sales'"),
    ("total_budget",
     "What is the total budget across all departments?",
     "SELECT sum(budget) FROM departments"),
    ("finance_headcount",
     "How many employees are in the Finance department?",
     "SELECT count(*) FROM employees e JOIN departments d ON d.id = e.department_id "
     "WHERE d.name = 'Finance'"),
    ("approved_expense_count",
     "How many expenses have been approved?",
     "SELECT count(*) FROM expenses WHERE status = 'approved'"),
    ("approved_expense_total",
     "What is the total amount of all approved expenses?",
     "SELECT sum(amount) FROM expenses WHERE status = 'approved'"),
    ("open_tickets",
     "How many tickets are currently open?",
     "SELECT count(*) FROM tickets WHERE status = 'open'"),
    ("avg_leave_balance",
     "What is the average leave balance across all employees, in days?",
     "SELECT avg(leave_balance_days) FROM employees"),
    ("engineering_salary_cost",
     "What is the total salary cost of the Engineering department?",
     "SELECT sum(e.salary) FROM employees e JOIN departments d ON d.id = e.department_id "
     "WHERE d.name = 'Engineering'"),
]


def gold_value(sql: str) -> float:
    """Run the gold SQL and return its single scalar result as a float."""
    rows = run_query(sql)
    value = next(iter(rows[0].values()))
    return float(value)


def numbers_in(text: str) -> list[float]:
    """Extract numeric tokens, ignoring thousands separators."""
    return [float(t) for t in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))]


def answer_matches(gold: float, text: str, rel: float = 0.01, abs_tol: float = 0.5) -> bool:
    tol = max(abs_tol, abs(gold) * rel)
    return any(abs(n - gold) <= tol for n in numbers_in(text))


async def run(limit: int | None, runs: int, delay: float) -> None:
    global _CAPTURING
    cases = CASES[:limit] if limit else CASES
    orchestrator, sub_agents, _it_mcp = build_agents()
    data_agent = sub_agents["data"]

    # LLM output is non-deterministic, so a single run is noisy. We repeat each
    # case `runs` times and report per-case reliability (passes / runs) — the
    # honest metric for a stochastic system. gold is computed once per case.
    gold = {cid: gold_value(sql) for cid, _q, sql in cases}
    tally = {cid: {"exec": 0, "ans": 0} for cid, _q, _sql in cases}

    print(f"Running {len(cases)} cases × {runs} run(s) against the Data Analyst agent...\n")
    for r in range(1, runs + 1):
        for cid, question, _sql in cases:
            g = gold[cid]
            _CAPTURED.clear()
            _CAPTURING = True
            try:
                resp = await data_agent.run(question, session=data_agent.create_session())
                answer, err = resp.text or "", None
            except Exception as e:  # keep going; record the failure
                answer, err = "", str(e)
            finally:
                _CAPTURING = False
            exec_ok = err is None and any(
                abs(v - g) <= max(0.5, abs(g) * 0.01) for v in _CAPTURED)
            ans_ok = err is None and answer_matches(g, answer)
            tally[cid]["exec"] += exec_ok
            tally[cid]["ans"] += ans_ok
            flag = "PASS" if exec_ok else "FAIL"
            print(f"[run {r}/{runs}] [{flag}] {cid:<26} exec={exec_ok} answer={ans_ok}"
                  + (f"  ({err[:80]})" if err else ""))
            if delay:  # pace requests to respect free-tier rate limits
                await asyncio.sleep(delay)

    trials = runs * len(cases)
    exec_pass = sum(t["exec"] for t in tally.values())
    ans_pass = sum(t["ans"] for t in tally.values())
    exec_acc = 100 * exec_pass / trials if trials else 0
    ans_acc = 100 * ans_pass / trials if trials else 0
    print(f"\nExecution accuracy: {exec_pass}/{trials} = {exec_acc:.1f}%  (over {runs} runs)")
    print(f"Answer match:       {ans_pass}/{trials} = {ans_acc:.1f}%")
    write_results(cases, gold, tally, runs, exec_pass, ans_pass, trials, exec_acc, ans_acc)


def write_results(cases, gold, tally, runs, exec_pass, ans_pass, trials, exec_acc, ans_acc) -> None:
    model = os.environ.get("OPENAI_CHAT_MODEL_ID") or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
    lines = [
        "# Text-to-SQL Eval Results",
        "",
        f"**Execution accuracy: {exec_pass}/{trials} = {exec_acc:.1f}%** &nbsp;·&nbsp; "
        f"Answer match: {ans_pass}/{trials} = {ans_acc:.1f}%",
        "",
        f"Model: `{model}` · {len(cases)} cases × {runs} runs = {trials} trials.",
        "",
        "- **Execution accuracy** (headline): a SQL query the agent actually ran "
        "returned the gold value. Standard text-to-SQL metric (cf. Spider); "
        "isolates SQL correctness from the model's narration.",
        "- **Answer match**: the gold value also survived into the agent's final "
        "natural-language answer.",
        "- Per-case columns show passes / runs — LLM output is non-deterministic, "
        "so a cell of 4/5 means that case passed 4 of 5 runs.",
        "",
        "Ground truth is computed live from the database via the gold SQL (never "
        "hardcoded). Tolerance 1% / 0.5. Reproduce: "
        "`python eval/run_eval.py --runs N`.",
        "",
        f"| # | id | exec ({runs}) | answer ({runs}) | gold |",
        "|---|----|------|--------|------|",
    ]
    for i, (cid, _q, _sql) in enumerate(cases, 1):
        lines.append(f"| {i} | `{cid}` | {tally[cid]['exec']}/{runs} | "
                     f"{tally[cid]['ans']}/{runs} | {gold[cid]:.2f} |")
    out = PROJECT_ROOT / "eval" / "RESULTS.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="run only the first N cases")
    ap.add_argument("--runs", type=int, default=1, help="repeat each case N times (default 1)")
    ap.add_argument("--delay", type=float, default=0.0,
                    help="seconds to sleep between cases (pace free-tier rate limits)")
    args = ap.parse_args()
    asyncio.run(run(args.limit, args.runs, args.delay))

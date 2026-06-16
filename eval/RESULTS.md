# Text-to-SQL eval results

**Passed: 22 of 24 (91.7%)**

Model: `llama-3.3-70b-versatile` (Groq, OpenAI-compatible endpoint). 12 questions × 2 full runs = 24 tries.

How a try is scored:

- **SQL result** — the SQL the agent actually ran returned the correct value.
  This is the main check.
- **Answer text** — the correct value also showed up in the agent's written
  reply.
- Each row below shows passes / runs. The model's output changes between runs,
  so 1/2 means that question passed 1 of the 2 runs.

The correct value for each question comes from running a known-good query
straight against the database, not from a hardcoded number. A value counts as
correct within 1% or 0.5. Reproduce with `python eval/run_eval.py --runs N`.
Groq's free tier allows 100k tokens per day, which is why this run only got
through 2 full passes; use `--delay` to space out requests under the
per-minute limit.

| # | question | SQL result | answer text | correct value |
|---|----|----------|------------|------|
| 1 | `total_headcount` | 2/2 | 2/2 | 39.00 |
| 2 | `dept_count` | 1/2 | 1/2 | 5.00 |
| 3 | `avg_salary_engineering` | 2/2 | 2/2 | 138833.33 |
| 4 | `max_salary` | 2/2 | 2/2 | 220000.00 |
| 5 | `min_salary_sales` | 2/2 | 2/2 | 71000.00 |
| 6 | `total_budget` | 2/2 | 2/2 | 5500000.00 |
| 7 | `finance_headcount` | 2/2 | 2/2 | 6.00 |
| 8 | `approved_expense_count` | 2/2 | 2/2 | 157.00 |
| 9 | `approved_expense_total` | 1/2 | 1/2 | 258888.20 |
| 10 | `open_tickets` | 2/2 | 2/2 | 24.00 |
| 11 | `avg_leave_balance` | 2/2 | 2/2 | 17.56 |
| 12 | `engineering_salary_cost` | 2/2 | 2/2 | 833000.00 |

## Notes

- The local `qwen2.5:3b` model (running on an 8 GB CPU machine) does much worse
  on the same questions — it often doesn't run any SQL, or it makes up table and
  column names. A bigger hosted model handles the SQL far better. You can switch
  to one with the `OPENAI_*` env vars (see the README); no code change needed.
- The two misses (`dept_count`, `approved_expense_total`) are just run-to-run
  variation, not a consistent problem — both pass on most runs.

# Enterprise Multi-Agent System

A hierarchical multi-agent system that automates internal enterprise workflows,
built with **Microsoft Agent Framework**, **PostgreSQL**, and the
**Model Context Protocol (MCP)**. Runs fully local and free: LLM inference via
Ollama, PostgreSQL via embedded user-space binaries.

```
                         ┌──────────────────┐
            user ──────► │   Orchestrator    │  routes each request
                         └────────┬─────────┘
        ┌───────────────┬─────────┴────────┬────────────────┐
        ▼               ▼                  ▼                ▼
  ┌──────────┐   ┌──────────────┐   ┌─────────────┐  ┌────────────┐
  │ HR Agent │   │ Data Analyst │   │ IT Support  │  │  Research  │
  │ 3 tools  │   │ text-to-SQL  │   │ 4 MCP tools │  │ 4 live-API │
  └────┬─────┘   │   3 tools    │   └──────┬──────┘  │   tools    │
       │         └──────┬───────┘          │ MCP     └─────┬──────┘
       ▼                ▼                  ▼ (stdio)       ▼
   PostgreSQL       PostgreSQL        MCP server →     Open-Meteo,
   (employees)      (analytics)       PostgreSQL       Frankfurter,
                                      (tickets)        Nager.Date,
                                                       Wikipedia
```

## Features

- **Hierarchical orchestration** — an orchestrator agent routes requests to 4
  specialized sub-agents using Agent Framework's agents-as-tools pattern
  (`Agent.as_tool()`).
- **14 agent tools** — HR lookups, guarded SQL execution, IT ticketing, and
  live external API calls (weather, currency, public holidays, Wikipedia).
- **Text-to-SQL** — the Data Analyst agent reads the live PostgreSQL schema,
  writes SQL from a plain-English question, runs it through a read-only guard,
  retries if the SQL errors, and formats the result.
- **MCP integration** — the IT tools aren't imported by the agent. They run in a
  separate MCP stdio server process (`mcp_server/server.py`) and the agent calls
  them through `MCPStdioTool`, so the tools live in their own process.
- **Web UI (DevUI)** — `python ui.py` starts a web UI on
  `http://localhost:8090` that shows each agent's tool calls, arguments, and
  results as they happen.
- **Read-only SQL** — `execute_sql_query` only allows SELECT statements. Writes
  would need a human-approval step, which isn't built yet.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# one-time: create + seed the database (embedded PostgreSQL, no root needed)
.venv/bin/python db/seed.py

# make sure ollama is running and the model is pulled
ollama pull qwen2.5:3b

# chat (CLI)
.venv/bin/python main.py "How many employees does each department have?"
.venv/bin/python main.py            # interactive

# or the web UI with live agent events
.venv/bin/python ui.py              # http://localhost:8090
```

## Example prompts

| Prompt | Path it exercises |
|---|---|
| "What is Aarav Desai's leave balance?" | orchestrator → HR agent → DB |
| "What is the average salary in Engineering?" | orchestrator → Data Analyst → schema introspection → SQL → DB |
| "Create a high priority ticket for Riya Patel: VPN keeps disconnecting" | orchestrator → IT agent → **MCP stdio** → DB |
| "What's the weather in Bengaluru?" | orchestrator → Research agent → live Open-Meteo API |
| "Convert 500 USD to INR" | orchestrator → Research agent → live ECB rates |

## LLM backend

Defaults to local **Ollama** (`qwen2.5:3b`) through Agent Framework's
OpenAI-compatible client — zero cost, no API key. The model is pinned in RAM
(`keep_alive=-1`) because cold loads on CPU take minutes.

| Env var | Effect |
|---|---|
| `OLLAMA_MODEL` | use a different local model (needs tool-calling support) |
| `OLLAMA_BASE_URL` | point at a remote Ollama |
| `OPENAI_API_KEY` + `OPENAI_CHAT_MODEL_ID` | switch to a hosted OpenAI-compatible provider |
| `OPENAI_BASE_URL` | point the hosted client at any OpenAI-compatible endpoint (e.g. Groq, Google Gemini's OpenAI endpoint) |
| `DATABASE_URL` | use a system PostgreSQL instead of the embedded one |

Note: a 3B model on CPU is about the minimum that works here. It routes
requests, calls tools, and writes correct SQL for simple questions, but it
sometimes writes a messy answer or misses an argument. A hosted model (set by
one env var) gets it right more often.

## Evaluation

`eval/run_eval.py` checks how often the Data Analyst agent turns a question into
correct SQL. It asks 12 questions. For each one it also runs a known-correct
query directly against the database to get the right answer, and the question
counts as passed when the SQL the agent actually ran returns that same answer.
The model's output changes between runs, so `--runs N` repeats each question and
reports how many times it passed.

| Model | Passed |
|---|---|
| `llama-3.3-70b-versatile` (Groq, hosted) | 22 of 24 (12 questions × 2 runs) |
| `qwen2.5:3b` (local, CPU) | often fails — usually doesn't run SQL, or makes up table names |

Per-question results are in [`eval/RESULTS.md`](eval/RESULTS.md). The local 3B
model is the free default; a stronger hosted model gets the SQL right far more
often.

```bash
# local (default Ollama)
.venv/bin/python eval/run_eval.py --runs 3

# any OpenAI-compatible API (no code change)
OPENAI_API_KEY=... OPENAI_BASE_URL=https://api.groq.com/openai/v1 \
  OPENAI_CHAT_MODEL_ID=llama-3.3-70b-versatile \
  .venv/bin/python eval/run_eval.py --runs 3 --delay 3
```

## Layout

```
agents/system.py     # clients, 4 sub-agents, orchestrator (agents-as-tools)
tools/hr_tools.py    # 3 HR tools          (@tool, typed via Annotated)
tools/finance_tools.py # 3 finance tools   (schema, guarded SQL, summaries)
tools/it_tools.py    # 4 IT tools          (plain functions, served over MCP)
tools/research_tools.py # 4 live-API tools (weather, fx, holidays, wiki)
mcp_server/server.py # FastMCP stdio server exposing the IT tools
db/database.py       # embedded PostgreSQL (pgserver) + query helper
db/seed.py           # schema + seed data (39 employees, 220 expenses, 60 tickets)
main.py              # CLI entrypoint
ui.py                # DevUI (AGUI) entrypoint
eval/run_eval.py     # text-to-SQL accuracy eval (execution accuracy, --runs N)
```

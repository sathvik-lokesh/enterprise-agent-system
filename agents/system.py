"""Hierarchical multi-agent system: 1 orchestrator + 4 specialized sub-agents.

LLM backend: local Ollama through Agent Framework's OpenAI-compatible client.
Set OLLAMA_MODEL / OLLAMA_BASE_URL to override; set OPENAI_API_KEY +
OPENAI_CHAT_MODEL_ID to use a hosted provider instead.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent_framework import Agent, MCPStdioTool
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient

from tools.hr_tools import get_employee_info, get_leave_balance, list_team
from tools.finance_tools import execute_sql_query, get_database_schema, get_expense_summary
from tools.research_tools import convert_currency, get_public_holidays, get_weather, lookup_topic

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")


def preload_model() -> None:
    """Load the model into RAM and pin it there (keep_alive=-1).

    On CPU-only machines a cold model load takes minutes; without pinning,
    Ollama evicts the model after ~5 idle minutes and every agent turn pays
    the reload cost again.
    """
    import httpx

    try:
        httpx.post(
            BASE_URL.replace("/v1", "/api/generate"),
            json={"model": MODEL, "keep_alive": -1},
            timeout=600,
        )
    except Exception:
        pass  # ollama not running yet; first real call will load the model


def make_client() -> OpenAIChatClient:
    # Hosted: any OpenAI-compatible provider. Set OPENAI_API_KEY, optionally
    # OPENAI_BASE_URL (e.g. Groq, Google Gemini's OpenAI endpoint) and
    # OPENAI_CHAT_MODEL_ID. Uses the Chat Completions API for broad provider
    # compatibility (the Responses API's previous_response_id field is rejected
    # by providers like Groq). Falls back to local Ollama when no key is set.
    if os.environ.get("OPENAI_API_KEY"):
        kwargs = {
            "model": os.environ.get("OPENAI_CHAT_MODEL_ID", "gpt-4o-mini"),
            "api_key": os.environ["OPENAI_API_KEY"],
        }
        if os.environ.get("OPENAI_BASE_URL"):
            kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
        return OpenAIChatCompletionClient(**kwargs)
    return OpenAIChatClient(model=MODEL, base_url=BASE_URL, api_key="ollama")


def make_it_mcp_tool() -> MCPStdioTool:
    """IT tools are consumed over the Model Context Protocol (stdio subprocess)."""
    return MCPStdioTool(
        name="it_support",
        command=sys.executable,
        args=[str(PROJECT_ROOT / "mcp_server" / "server.py")],
    )


def build_agents() -> tuple[Agent, dict[str, Agent], MCPStdioTool]:
    """Returns (orchestrator, sub_agents, it_mcp_tool).

    Enter the returned MCP tool with `async with` (or call `await tool.close()`
    on shutdown) so the stdio subprocess is torn down in the task that
    created it.
    """
    preload_model()
    hr_agent = Agent(
        client=make_client(),
        name="hr_agent",
        description="Answers HR questions: employee profiles, leave balances, team rosters.",
        instructions=(
            "You are the HR assistant for AcmeCorp. Use your tools to answer questions "
            "about employees, leave balances and teams. Always base answers on tool "
            "results, never invent employee data. Be concise."
        ),
        tools=[get_employee_info, get_leave_balance, list_team],
    )

    data_agent = Agent(
        client=make_client(),
        name="data_analyst_agent",
        description=(
            "Answers analytics questions by translating natural language to SQL and "
            "running it on the company PostgreSQL database (salaries, budgets, "
            "expenses, headcount, tickets)."
        ),
        instructions=(
            "You are a data analyst with read-only SQL access to the AcmeCorp "
            "PostgreSQL database. You MUST follow this exact workflow:\n"
            "1. Call get_database_schema to see the tables and columns.\n"
            "2. Write ONE PostgreSQL SELECT query for the user's question. Note: "
            "employees link to departments via employees.department_id = departments.id.\n"
            "3. Call execute_sql_query to run it.\n"
            "4. If you get SQL ERROR, fix the query and call execute_sql_query AGAIN "
            "with the fixed query. NEVER show a query to the user without executing it.\n"
            "5. Your final answer must contain the actual numbers returned by "
            "execute_sql_query, plus the SQL you ran. Never fabricate numbers, and "
            "never answer before execute_sql_query has returned rows."
        ),
        tools=[get_database_schema, execute_sql_query, get_expense_summary],
    )

    it_mcp = make_it_mcp_tool()
    it_agent = Agent(
        client=make_client(),
        name="it_support_agent",
        description=(
            "Handles IT support: creating tickets, checking ticket status, listing "
            "open tickets, and checking system status (email/vpn/wifi/jira/github)."
        ),
        instructions=(
            "You are the IT support assistant. Use your MCP tools to create tickets, "
            "look up ticket status and check system health. When the user states a "
            "priority (low/medium/high), pass it as the priority argument. Confirm "
            "ticket IDs back to the user. Be concise."
        ),
        tools=[it_mcp],
    )

    research_agent = Agent(
        client=make_client(),
        name="research_agent",
        description=(
            "Fetches live external data: weather, currency conversion, public "
            "holidays, and general topic lookups."
        ),
        instructions=(
            "You are a research assistant with live data tools. Use them for "
            "weather, currency, holidays and factual lookups. Quote the data you "
            "received; do not guess. Be concise."
        ),
        tools=[get_weather, convert_currency, get_public_holidays, lookup_topic],
    )

    sub_agents = {
        "hr": hr_agent,
        "data": data_agent,
        "it": it_agent,
        "research": research_agent,
    }

    orchestrator = Agent(
        client=make_client(),
        name="orchestrator",
        description="Routes enterprise requests to specialized sub-agents.",
        instructions=(
            "You are the AcmeCorp enterprise assistant orchestrator. You do not "
            "answer domain questions yourself — delegate to exactly the right "
            "sub-agent tool:\n"
            "- hr_agent: employee profiles, leave balances, team rosters\n"
            "- data_analyst_agent: analytics/aggregate questions needing SQL "
            "(salaries, budgets, expenses, counts, averages)\n"
            "- it_support_agent: IT tickets and system status\n"
            "- research_agent: weather, currency, holidays, general topics\n"
            "When calling a sub-agent, the task argument MUST contain the user's "
            "complete question verbatim — never a vague summary like 'data analysis "
            "request'. If a request spans domains, call multiple sub-agents and "
            "combine their answers. Return the sub-agent's answer to the user "
            "concisely; do not ask the user clarifying questions a sub-agent could "
            "answer."
        ),
        tools=[
            hr_agent.as_tool(
                arg_description="The user's complete HR question, verbatim"),
            data_agent.as_tool(
                arg_description="The user's complete analytics question, verbatim"),
            it_agent.as_tool(
                arg_description="The user's complete IT request, verbatim, including any stated priority"),
            research_agent.as_tool(
                arg_description="The user's complete research question, verbatim"),
        ],
    )
    return orchestrator, sub_agents, it_mcp

"""Finance / text-to-SQL tools (3): schema introspection, guarded SQL execution,
expense summaries. The text-to-SQL pipeline is: agent reads the schema with
get_database_schema, writes SQL, executes it with execute_sql_query, then
formats the rows for the user."""

import json
import re
import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_framework import tool

from db.database import run_query

# Read-only guard: the agent may only run SELECT statements. Writes would go
# through a Human-in-the-Loop approval flow instead (see README).
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy)\b", re.I
)


@tool
def get_database_schema() -> str:
    """Return the full database schema (tables, columns, types). ALWAYS call this
    first before writing any SQL query, so column and table names are correct."""
    rows = run_query(
        """SELECT table_name, column_name, data_type
           FROM information_schema.columns
           WHERE table_schema = 'public'
           ORDER BY table_name, ordinal_position"""
    )
    schema: dict[str, list[str]] = {}
    for r in rows:
        schema.setdefault(r["table_name"], []).append(f"{r['column_name']} ({r['data_type']})")
    return json.dumps(schema, indent=1)


@tool
def execute_sql_query(
    sql: Annotated[str, "A single read-only PostgreSQL SELECT statement"],
) -> str:
    """Execute a read-only SQL SELECT query against the company PostgreSQL database
    and return the rows as JSON. Use for analytics questions (salaries, budgets,
    expenses, counts, averages). Call get_database_schema first."""
    stripped = sql.strip().rstrip(";")
    if not stripped.lower().startswith(("select", "with")):
        return "REJECTED: only SELECT queries are allowed."
    if _FORBIDDEN.search(stripped):
        return "REJECTED: query contains a write/DDL keyword. Only read-only SELECTs are allowed."
    try:
        rows = run_query(stripped + " LIMIT 50" if " limit " not in stripped.lower() else stripped)
    except Exception as e:
        return f"SQL ERROR: {e}. Fix the query and try again (check the schema)."
    return json.dumps(rows[:50], default=str)


@tool
def get_expense_summary(
    group_by: Annotated[str, "One of: 'category', 'status', 'department'"] = "category",
) -> str:
    """Get a pre-built summary of company EXPENSES (reimbursements) grouped by
    category, status, or department. ONLY for expense questions — never use this
    for salary, headcount, or budget questions (use SQL for those)."""
    if group_by == "department":
        sql = """SELECT d.name AS department, count(*) AS n, round(sum(x.amount),2) AS total
                 FROM expenses x JOIN employees e ON e.id = x.employee_id
                 JOIN departments d ON d.id = e.department_id
                 GROUP BY d.name ORDER BY total DESC"""
    elif group_by == "status":
        sql = """SELECT status, count(*) AS n, round(sum(amount),2) AS total
                 FROM expenses GROUP BY status ORDER BY total DESC"""
    else:
        sql = """SELECT category, count(*) AS n, round(sum(amount),2) AS total
                 FROM expenses GROUP BY category ORDER BY total DESC"""
    return json.dumps(run_query(sql), default=str)

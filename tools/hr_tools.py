"""HR domain tools (3): employee lookup, leave balance, team listing."""

import json
import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_framework import tool

from db.database import run_query


@tool
def get_employee_info(
    name: Annotated[str, "Full or partial employee name, e.g. 'Priya' or 'Priya Sharma'"],
) -> str:
    """Look up an employee's profile: title, department, manager, email and hire date.
    Call this when the user asks about a specific person."""
    rows = run_query(
        """SELECT e.id, e.name, e.email, e.title, d.name AS department,
                  m.name AS manager, e.hire_date::text
           FROM employees e
           JOIN departments d ON d.id = e.department_id
           LEFT JOIN employees m ON m.id = e.manager_id
           WHERE e.name ILIKE %s ORDER BY e.name LIMIT 5""",
        (f"%{name}%",),
    )
    if not rows:
        return f"No employee found matching '{name}'."
    return json.dumps(rows, default=str)


@tool
def get_leave_balance(
    name: Annotated[str, "Full or partial employee name"],
) -> str:
    """Get an employee's remaining leave balance in days. Call this for
    vacation/PTO/leave questions about a specific person."""
    rows = run_query(
        "SELECT name, leave_balance_days FROM employees WHERE name ILIKE %s LIMIT 5",
        (f"%{name}%",),
    )
    if not rows:
        return f"No employee found matching '{name}'."
    return json.dumps(rows)


@tool
def list_team(
    department: Annotated[str, "Department name, e.g. 'Engineering', 'Sales', 'Finance'"],
) -> str:
    """List all employees in a department with their titles. Call this for
    questions about who works in a team or department headcount."""
    rows = run_query(
        """SELECT e.name, e.title, e.email
           FROM employees e JOIN departments d ON d.id = e.department_id
           WHERE d.name ILIKE %s ORDER BY e.name""",
        (f"%{department}%",),
    )
    if not rows:
        return f"No department found matching '{department}'."
    return json.dumps(rows)

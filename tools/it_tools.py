"""IT support tools (4): ticket create/status/list + system status.
These are also exposed over MCP by mcp_server/server.py."""

import json
import random
import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import run_query


def create_ticket(
    employee_name: Annotated[str, "Name of the employee reporting the issue"],
    category: Annotated[str, "One of: laptop, vpn, email, access request, software install, printer"],
    subject: Annotated[str, "Short description of the issue"],
    priority: Annotated[str, "low, medium, or high"] = "medium",
) -> str:
    """Create a new IT support ticket for an employee and return its ticket ID."""
    emp = run_query("SELECT id, name FROM employees WHERE name ILIKE %s LIMIT 1",
                    (f"%{employee_name}%",))
    if not emp:
        return f"No employee found matching '{employee_name}'."
    if priority not in ("low", "medium", "high"):
        priority = "medium"
    rows = run_query(
        """INSERT INTO tickets (employee_id, category, priority, status, subject)
           VALUES (%s, %s, %s, 'open', %s) RETURNING id""",
        (emp[0]["id"], category, priority, subject),
    )
    return json.dumps({"ticket_id": rows[0]["id"], "employee": emp[0]["name"],
                       "status": "open", "priority": priority})


def get_ticket_status(
    ticket_id: Annotated[int, "Numeric ticket ID"],
) -> str:
    """Get the current status and details of an IT ticket by its ID."""
    rows = run_query(
        """SELECT t.id, e.name AS employee, t.category, t.priority, t.status,
                  t.subject, t.created_at::text, t.resolved_at::text
           FROM tickets t JOIN employees e ON e.id = t.employee_id WHERE t.id = %s""",
        (ticket_id,),
    )
    if not rows:
        return f"No ticket with id {ticket_id}."
    return json.dumps(rows[0], default=str)


def list_open_tickets(
    priority: Annotated[str, "Optional filter: low, medium, high, or 'all'"] = "all",
) -> str:
    """List currently open IT tickets, optionally filtered by priority."""
    if priority in ("low", "medium", "high"):
        rows = run_query(
            """SELECT t.id, e.name AS employee, t.category, t.priority, t.subject
               FROM tickets t JOIN employees e ON e.id = t.employee_id
               WHERE t.status = 'open' AND t.priority = %s ORDER BY t.created_at DESC LIMIT 20""",
            (priority,),
        )
    else:
        rows = run_query(
            """SELECT t.id, e.name AS employee, t.category, t.priority, t.subject
               FROM tickets t JOIN employees e ON e.id = t.employee_id
               WHERE t.status = 'open' ORDER BY t.created_at DESC LIMIT 20""")
    return json.dumps(rows, default=str)


def check_system_status(
    system: Annotated[str, "One of: email, vpn, wifi, jira, github, all"] = "all",
) -> str:
    """Check the operational status of internal IT systems (email, vpn, wifi, jira, github)."""
    # Simulated status page; deterministic per day so answers are stable.
    systems = ["email", "vpn", "wifi", "jira", "github"]
    rng = random.Random("statuspage")
    statuses = {s: rng.choices(["operational", "degraded"], weights=[90, 10])[0] for s in systems}
    if system != "all" and system in statuses:
        return json.dumps({system: statuses[system]})
    return json.dumps(statuses)

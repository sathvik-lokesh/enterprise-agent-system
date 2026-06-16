"""Create and seed the enterprise schema. Idempotent — drops and recreates."""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import get_conn

SCHEMA = """
DROP TABLE IF EXISTS expenses, tickets, employees, departments CASCADE;

CREATE TABLE departments (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    budget      NUMERIC(12,2) NOT NULL
);

CREATE TABLE employees (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL,
    department_id INT REFERENCES departments(id),
    manager_id  INT REFERENCES employees(id),
    salary      NUMERIC(10,2) NOT NULL,
    hire_date   DATE NOT NULL,
    leave_balance_days INT NOT NULL DEFAULT 20
);

CREATE TABLE expenses (
    id          SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id),
    category    TEXT NOT NULL,
    amount      NUMERIC(10,2) NOT NULL,
    expense_date DATE NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    description TEXT
);

CREATE TABLE tickets (
    id          SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id),
    category    TEXT NOT NULL,
    priority    TEXT NOT NULL DEFAULT 'medium',
    status      TEXT NOT NULL DEFAULT 'open',
    subject     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    resolved_at TIMESTAMP
);
"""

DEPARTMENTS = [
    ("Engineering", 2_500_000),
    ("Sales", 1_200_000),
    ("Human Resources", 400_000),
    ("Finance", 600_000),
    ("Marketing", 800_000),
]

FIRST = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Karthik", "Divya",
         "Arjun", "Meera", "Sanjay", "Pooja", "Rahul", "Kavya", "Nikhil", "Ishita",
         "Aditya", "Riya", "Suresh", "Lakshmi", "Mohan", "Tanvi", "Deepak", "Nisha"]
LAST = ["Sharma", "Patel", "Reddy", "Iyer", "Gupta", "Nair", "Singh", "Rao",
        "Mehta", "Joshi", "Kulkarni", "Desai"]

TITLES = {
    "Engineering": ["Software Engineer", "Senior Software Engineer", "Staff Engineer", "Engineering Manager"],
    "Sales": ["Account Executive", "Sales Manager", "SDR"],
    "Human Resources": ["HR Specialist", "HR Manager", "Recruiter"],
    "Finance": ["Financial Analyst", "Accountant", "Finance Manager"],
    "Marketing": ["Marketing Specialist", "Content Manager", "Growth Manager"],
}

EXPENSE_CATEGORIES = ["travel", "meals", "software", "hardware", "training", "office supplies"]
TICKET_CATEGORIES = ["laptop", "vpn", "email", "access request", "software install", "printer"]


def seed():
    random.seed(42)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)

        for name, budget in DEPARTMENTS:
            cur.execute("INSERT INTO departments (name, budget) VALUES (%s, %s)", (name, budget))

        cur.execute("SELECT id, name FROM departments")
        depts = cur.fetchall()

        used_names = set()
        emp_ids = []
        for dept_id, dept_name in depts:
            n = random.randint(6, 10)
            manager_id = None
            for i in range(n):
                while True:
                    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
                    if name not in used_names:
                        used_names.add(name)
                        break
                email = name.lower().replace(" ", ".") + "@acmecorp.com"
                title = TITLES[dept_name][min(i, len(TITLES[dept_name]) - 1)] if i < 2 \
                    else random.choice(TITLES[dept_name][:-1] or TITLES[dept_name])
                if i == 0:
                    title = TITLES[dept_name][-1]  # first hire in dept is the manager
                salary = random.randint(60, 220) * 1000
                hire_date = date(2018, 1, 1) + timedelta(days=random.randint(0, 2800))
                cur.execute(
                    """INSERT INTO employees (name, email, title, department_id, manager_id,
                       salary, hire_date, leave_balance_days)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (name, email, title, dept_id, manager_id, salary, hire_date,
                     random.randint(2, 30)),
                )
                eid = cur.fetchone()[0]
                if i == 0:
                    manager_id = eid
                emp_ids.append(eid)

        for _ in range(220):
            cur.execute(
                """INSERT INTO expenses (employee_id, category, amount, expense_date, status, description)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (random.choice(emp_ids), random.choice(EXPENSE_CATEGORIES),
                 round(random.uniform(15, 3500), 2),
                 date(2025, 1, 1) + timedelta(days=random.randint(0, 500)),
                 random.choices(["approved", "pending", "rejected"], weights=[70, 20, 10])[0],
                 None),
            )

        for _ in range(60):
            status = random.choices(["open", "in_progress", "resolved"], weights=[30, 20, 50])[0]
            cur.execute(
                """INSERT INTO tickets (employee_id, category, priority, status, subject, created_at, resolved_at)
                   VALUES (%s,%s,%s,%s,%s, now() - (%s || ' days')::interval,
                           CASE WHEN %s = 'resolved' THEN now() - (%s || ' days')::interval ELSE NULL END)""",
                (random.choice(emp_ids), random.choice(TICKET_CATEGORIES),
                 random.choice(["low", "medium", "high"]), status,
                 f"Issue with {random.choice(TICKET_CATEGORIES)}",
                 random.randint(1, 90), status, random.randint(0, 30)),
            )

        conn.commit()

    print("Database seeded.")


if __name__ == "__main__":
    seed()

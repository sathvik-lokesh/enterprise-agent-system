"""PostgreSQL access layer.

Uses pgserver (embedded PostgreSQL binaries, runs in user space) so the
project needs no root install. Swap PG_URI via the DATABASE_URL env var
to point at a system PostgreSQL instead.
"""

import os
import threading
from pathlib import Path

import pgserver
import psycopg

PGDATA = Path(__file__).resolve().parent / "pgdata"

_server = None
# pgserver.get_server is not safe to call concurrently (parallel tool calls
# race on the postmaster lock), so serialize first-time startup.
_lock = threading.Lock()


def get_uri() -> str:
    global _server
    env_uri = os.environ.get("DATABASE_URL")
    if env_uri:
        return env_uri
    with _lock:
        if _server is None:
            _server = pgserver.get_server(str(PGDATA))
        return _server.get_uri()


def get_conn() -> psycopg.Connection:
    return psycopg.connect(get_uri())


def run_query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a query and return rows as dicts."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

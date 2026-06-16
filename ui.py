"""Launch the Agent Framework DevUI (AGUI) — a web UI that shows the
conversation plus live agent events (tool calls, arguments, results),
useful for demos and for Human-in-the-Loop inspection.

Usage:  python ui.py        then open http://localhost:8090
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_framework_devui import serve

from db.database import get_uri
from agents.system import build_agents


def main() -> None:
    get_uri()  # start embedded PostgreSQL before agents take requests
    orchestrator, sub_agents, _ = build_agents()
    # Expose the orchestrator and each sub-agent as selectable entities.
    serve(
        entities=[orchestrator, *sub_agents.values()],
        port=8090,
        auto_open=False,
        auth_enabled=False,
    )


if __name__ == "__main__":
    main()

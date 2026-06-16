"""CLI chat with the enterprise multi-agent system.

Usage:
  python main.py                 # interactive chat
  python main.py "one question"  # single-shot
"""

import asyncio
import sys

from agents.system import build_agents


async def main() -> None:
    orchestrator, _, it_mcp = build_agents()
    session = orchestrator.create_session()

    async with it_mcp:  # owns the MCP stdio subprocess lifecycle
        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
            resp = await orchestrator.run(question, session=session)
            print(resp.text)
            return

        print("AcmeCorp Enterprise Assistant (ctrl-d to exit)")
        while True:
            try:
                q = input("\nyou> ").strip()
            except EOFError:
                break
            if not q:
                continue
            resp = await orchestrator.run(q, session=session)
            print(f"\nassistant> {resp.text}")


if __name__ == "__main__":
    asyncio.run(main())

"""MCP stdio server exposing the IT support tools.

The IT Support agent does not import these functions directly — it connects to
this server over the Model Context Protocol (stdio transport) via MCPStdioTool,
so the tools could equally live in another process, language, or machine.

Run standalone for testing:  python mcp_server/server.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from tools.it_tools import (
    check_system_status,
    create_ticket,
    get_ticket_status,
    list_open_tickets,
)

mcp = FastMCP("it-support")

mcp.tool()(create_ticket)
mcp.tool()(get_ticket_status)
mcp.tool()(list_open_tickets)
mcp.tool()(check_system_status)

if __name__ == "__main__":
    mcp.run(transport="stdio")

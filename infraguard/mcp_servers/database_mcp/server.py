from __future__ import annotations

import argparse
import os

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings


mcp = MCPServer("InfraGuard Database MCP")


@mcp.tool()
def read_lock_snapshot(database: str = "payments") -> dict[str, object]:
    """Return a read-only lock contention snapshot."""
    print(f"[MCP] read_lock_snapshot EXECUTED database={database}", flush=True)
    return {
        "database": database,
        "blocked_sessions": 17,
        "oldest_wait_seconds": 42,
        "write_action_available": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InfraGuard Database MCP")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8003")), help="Port to listen on")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="Host to bind")
    args = parser.parse_args()

    security_settings = TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )

    mcp.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        transport_security=security_settings,
    )

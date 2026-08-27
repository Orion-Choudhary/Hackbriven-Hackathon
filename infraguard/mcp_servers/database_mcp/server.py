from __future__ import annotations

from mcp.server.mcpserver import MCPServer


mcp = MCPServer("InfraGuard Database MCP")


@mcp.tool()
def read_lock_snapshot(database: str = "payments") -> dict[str, object]:
    """Return a read-only lock contention snapshot."""
    return {
        "database": database,
        "blocked_sessions": 17,
        "oldest_wait_seconds": 42,
        "write_action_available": False,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

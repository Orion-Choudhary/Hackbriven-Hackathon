from __future__ import annotations

from mcp.server.mcpserver import MCPServer


mcp = MCPServer("InfraGuard Remediation MCP")


@mcp.tool()
def restart_payment_service(environment: str = "staging", force: bool = False) -> dict[str, object]:
    """Restart the payment service in an explicitly selected environment."""
    return {
        "service": "payments-api",
        "environment": environment,
        "force": force,
        "status": "restart_requested",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

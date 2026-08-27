from __future__ import annotations

import argparse
import os

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings


mcp = MCPServer("InfraGuard Remediation MCP")


@mcp.tool()
def restart_payment_service(environment: str = "staging", force: bool = False) -> dict[str, object]:
    """Restart the payment service in an explicitly selected environment."""
    print(
        f"[MCP] restart_payment_service EXECUTED environment={environment} force={force}",
        flush=True,
    )
    return {
        "service": "payments-api",
        "environment": environment,
        "force": force,
        "status": "restart_requested",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InfraGuard Remediation MCP")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8002")), help="Port to listen on")
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

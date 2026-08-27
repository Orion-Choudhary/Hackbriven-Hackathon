from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
import uvicorn

mcp = MCPServer("InfraGuard Test MCP")


@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back to the caller."""
    return f"echo: {message}"


transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)

app = mcp.streamable_http_app(
    transport_security=transport_security,
    host="0.0.0.0",
)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
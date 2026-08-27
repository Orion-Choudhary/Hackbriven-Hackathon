# Architecture

```text
User alert
  -> Commander
  -> ArmorIQ capture_plan/get_intent_token
  -> delegated Diagnostic and Remediation authority
  -> ArmorIQ Proxy /invoke
  -> registered MCP tool
```

Commander owns the incident plan. Diagnostic owns read-only investigation. Remediation owns bounded recovery actions.

The MCP `/mcp` path is the Streamable HTTP transport endpoint. ArmorIQ SDK invocations go to the ArmorIQ proxy `/invoke` endpoint, which then routes to the registered MCP.

## Authorization Model

Diagnostic scope:

```text
diagnostic_mcp.fetch_system_logs
diagnostic_mcp.query_metrics
```

Remediation scope:

```text
remediation_mcp.restart_payment_service
```

The content Diagnostic reads can influence its reasoning, but it does not expand Diagnostic's delegated authority.

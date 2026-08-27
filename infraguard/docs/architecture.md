# Architecture

## Overview

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

## Verified Behavior

- ArmorIQ SDK v2 is installed and importable as `armoriq_sdk`.
- `ArmorIQClient.from_config()` loads the YAML configuration.
- `capture_plan()` successfully creates plan captures.
- `get_intent_token()` successfully mints tokens against the cloud backend.
- `delegate()` exists with signature:
  `(intent_token, delegate_public_key, validity_seconds, allowed_actions, target_agent, subtask) -> DelegationResult`
- `delegate()` posts to `{backend_endpoint}/iap/trust/delegate`.
- `list_mcps()` queries `GET {backend}/mcp/my-servers`.
- `get_mcp_tool_schemas()` retrieves registered tool schemas.
- `invoke()` posts to `{proxy_endpoint}/invoke`.
- The SDK enforces that the requested action exists in the captured plan before sending the request.
- The proxy health endpoint returns 200.
- Local delegation tests pass with `LocalAuthorizationGateway`.

## Assumed Behavior (Pending Experimental Confirmation)

- Delegated token `allowed_actions` semantics are enforced server-side by ArmorIQ proxy. Client-side `LocalAuthorizationGateway` simulates this, but the exact ArmorIQ proxy enforcement for delegated tokens must be verified.
- `delegate_subtree()` may be preferred over `delegate()` for subtree-bounded delegation.
- Delegated token contents and exact response keys may vary by backend version.
- `armoriq register` works against the current cloud control plane with the provided configuration.
- Cloudflare Quick Tunnels are acceptable for development but should not be treated as production deployment architecture.

## Known Integration Issues

- Proxy invocation currently returns `404 Not Found` from `https://proxy.armoriq.ai/invoke` in our testing environment, even though registration, tool discovery, and token issuance succeed. The exact cause is unproven. Potential causes include proxy routing/registration mismatch, MCP registration state, Cloudflare tunnel behavior, or environment mismatch.
- PowerShell and Conda shells can resolve different endpoint environments. Always verify endpoints in the same shell used to run the application.
- The `armoriq-test.yaml` / config API key must be provided via environment variable; do not hardcode secrets in YAML.

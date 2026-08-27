# InfraGuard

InfraGuard is a least-privilege authorization demo for autonomous incident-response agents.

Core message:

> The agent's reasoning can be compromised. Its authority cannot.

The demo models a FinSecure payment outage where Diagnostic reads poisoned logs and tries to restart a service. Diagnostic only receives authority for diagnostic tools, so the restart attempt is denied. Remediation receives separate authority for the staging restart.

## Quick Start

```powershell
cd infraguard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
```

Run the local demo paths:

```powershell
python -m infraguard.agents.commander.main
python -m infraguard.agents.diagnostic.main
python -m infraguard.agents.remediation.main
```

## ArmorIQ SDK v2

The project uses:

```python
from armoriq_sdk import ArmorIQClient
```

The expected SDK flow is:

```text
capture_plan()
get_intent_token()
delegate()
invoke()
```

`get_intent_token()` talks to the ArmorIQ backend/IAP token endpoint. `invoke()` talks to `{proxy_endpoint}/invoke`; it should not be changed to call an MCP `/mcp` URL directly.

Set credentials in your shell, not in Git:

```powershell
$env:ARMORIQ_API_KEY="YOUR_KEY"
$env:BACKEND_ENDPOINT="https://api.armoriq.ai"
$env:IAP_ENDPOINT="https://iap.armoriq.ai"
$env:PROXY_ENDPOINT="https://proxy.armoriq.ai"
```

Verify endpoints in the same shell used to run the SDK:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq/armoriq.yaml'); print('backend:', c.backend_endpoint); print('iap:', c.iap_endpoint); print('proxy:', c.default_proxy_endpoint)"
```

## Current Caution

Registration, tool discovery, and token issuance are separate from proxy execution. A `404 Not Found` from `https://proxy.armoriq.ai/invoke` should be investigated as a proxy routing, registration, deployment, or networking issue. Do not claim it is definitely caused by Cloudflare without evidence.

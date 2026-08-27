Yes. Based on everything we established, here is a consolidated **ArmorIQ SDK v2 integration guide + team onboarding guide** you can put directly into your GitHub repo.

# InfraGuard × ArmorIQ SDK v2

## 1. What we have established

The project is using the **ArmorIQ Python SDK v2**, not the older v1/FastMCP integration.

The working architecture is:

```text
Your application
      │
      │ ArmorIQClient
      ▼
ArmorIQ Backend / IAP
      │
      │ Intent Token
      ▼
ArmorIQ Proxy
      │
      │ MCP invocation
      ▼
Registered MCP Server
      │
      ▼
MCP Tool
```

For our test environment:

```text
MCP Server
https://<dynamic-cloudflare-host>.trycloudflare.com/mcp
        │
        ▼
ArmorIQ Control Plane
https://api.armoriq.ai
        │
        ├── IAP
        │   https://iap.armoriq.ai
        │
        └── Proxy
            https://proxy.armoriq.ai
```

# 2. Important SDK v2 distinction

Do **not** build against examples using:

```python
from fastmcp import FastMCP
```

Those examples correspond to the older FastMCP/v1-style integration we initially considered.

Our installed SDK exposes:

```python
from mcp.server.mcpserver import MCPServer
```

and:

```python
mcp.run(transport="streamable-http")
```

We verified that this works with our SDK version.

# 3. Building an MCP server

The minimal working MCP server is:

```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("InfraGuard Test MCP")

@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back to the caller."""
    return f"echo: {message}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

Run it:

```powershell
python server.py
```

It starts on:

```text
http://0.0.0.0:8000
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

### Important

The server's `/mcp` path is required for the Streamable HTTP MCP transport.

A request to:

```text
http://localhost:8000/
```

returns:

```text
404 Not Found
```

That is expected.

# 4. Cloudflare tunnel

For external access during development, we used Cloudflare Tunnel.

Conceptually:

```text
Cloudflare
     │
     ▼
https://random-name.trycloudflare.com
     │
     ▼
localhost:8000
```

The public MCP endpoint is therefore:

```text
https://random-name.trycloudflare.com/mcp
```

### Critical observation

The Cloudflare hostname changes when using an ephemeral:

```text
trycloudflare.com
```

tunnel.

Therefore **never hardcode the hostname into application code**.

For development, the URL belongs in configuration:

```yaml
mcp_servers:
  - id: trycloudflare
    url: https://CURRENT-CLOUDFLARE-HOST.trycloudflare.com
    auth: none
```

When the tunnel changes, update the configuration and re-register.

# 5. Why we saw the `Invalid Host header` / 421 error

Earlier we saw:

```text
WARNING Invalid Host header:
south-airfare-midlands-add.trycloudflare.com

421 Misdirected Request
```

This came from the MCP server's transport security layer.

The local MCP server was receiving a request whose `Host` header was the Cloudflare hostname rather than its local host.

This is related to the Streamable HTTP transport's host validation.

We subsequently got the MCP server working sufficiently for ArmorIQ to discover:

```text
1 tools discovered:
    echo
```

So the important conclusion is:

> **The MCP server itself and Streamable HTTP transport are working.**

# 6. Verifying the MCP server directly

This request:

```powershell
python -c "import httpx; u='https://YOUR-CLOUDFLARE-HOST.trycloudflare.com/mcp'; r=httpx.get(u, timeout=15); print(r.status_code); print(r.text[:1000])"
```

returned:

```text
400
{"jsonrpc":"2.0","id":null,"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}
```

This is actually useful.

It tells us:

- Cloudflare reaches the server.
- `/mcp` exists.
- The MCP Streamable HTTP transport is active.
- The request is being interpreted as MCP.
- A plain GET isn't a valid way to start/use the MCP session.

Therefore **do not interpret that 400 as "the MCP server is broken."**

# 7. ArmorIQ configuration

Our working configuration structure is:

```yaml
version: v1

identity:
  api_key: YOUR_ARMORIQ_API_KEY
  user_id: YOUR_USER_ID
  agent_id: YOUR_AGENT_ID

environment: sandbox

proxy:
  url: https://proxy.armoriq.ai
  timeout: 30
  max_retries: 3

mcp_servers:
  - id: trycloudflare
    url: https://YOUR-CLOUDFLARE-HOST.trycloudflare.com
    auth: none

policy:
  allow:
    - trycloudflare.echo
  deny: []

intent:
  ttl_seconds: 300
  require_csrg: true
```

### Never commit the real API key

The actual key that appeared during development should be treated as a secret.

If it was ever pushed to GitHub, **rotate/revoke it immediately**.

Use something like:

```yaml
identity:
  api_key: ${ARMORIQ_API_KEY}
```

if your configuration loader supports environment interpolation, or otherwise use your team's approved secret mechanism.

At minimum:

```text
armoriq-test.yaml
.env
```

should be in `.gitignore` if they contain secrets.

# 8. ArmorIQ CLI

The installed CLI is:

```text
armoriq
```

Help:

```powershell
armoriq --help
```

Commands we confirmed:

```text
init
validate
register
status
logs
login
logout
whoami
orgs
switch-org
keys
policy
```

# 9. Initializing a configuration

Run:

```powershell
armoriq init
```

Or:

```powershell
armoriq init --output armoriq-test.yaml
```

The CLI asks for the MCP server URL.

For development:

```text
https://CURRENT-CLOUDFLARE-HOST.trycloudflare.com
```

It successfully verified the server and discovered:

```text
1 tools discovered:
    echo
```

# 10. Validate before registering

Always run:

```powershell
armoriq validate --config armoriq-test.yaml
```

The successful result was:

```text
✓ Config syntax valid
✓ API key authenticated
✓ trycloudflare MCP reachable (1 tools)
✓ Policy references valid tool names
Ready to register.
```

This should be a mandatory step for every developer.

# 11. Registering

Then:

```powershell
armoriq register --config armoriq-test.yaml
```

Successful registration produced:

```text
✓ Agent Test registered
✓ MCP server trycloudflare registered (1 tools)
✓ Policy applied (1 allowed, 0 denied)
✓ Proxy endpoint: https://proxy.armoriq.ai
```

After registration:

```powershell
armoriq status
```

showed:

```text
Agent: Test
User: Test-services
Environment: sandbox
Proxy endpoint: https://proxy.armoriq.ai
MCP servers: trycloudflare
```

# 12. SDK initialization

The primary application interface is:

```python
from armoriq_sdk import ArmorIQClient
```

Then:

```python
client = ArmorIQClient.from_config("armoriq-test.yaml")
```

We verified this works.

# 13. The important SDK endpoints

The SDK internally resolved these endpoints:

### Production/cloud configuration

```text
Backend:
https://api.armoriq.ai

IAP:
https://iap.armoriq.ai

Proxy:
https://proxy.armoriq.ai
```

### Local defaults

The SDK contains local defaults including:

```text
Backend:
http://127.0.0.1:3000

IAP:
http://127.0.0.1:8080

Proxy:
http://127.0.0.1:3001
```

This distinction became extremely important during debugging.

# 14. PowerShell vs Conda terminal problem

We discovered that two shells were using different endpoint environments.

### PowerShell

We explicitly set:

```powershell
$env:BACKEND_ENDPOINT="https://api.armoriq.ai"
$env:IAP_ENDPOINT="https://iap.armoriq.ai"
$env:PROXY_ENDPOINT="https://proxy.armoriq.ai"
```

and obtained:

```text
backend: https://api.armoriq.ai
iap: https://iap.armoriq.ai
proxy: https://proxy.armoriq.ai
```

### Conda terminal

The same SDK configuration produced:

```text
backend: http://127.0.0.1:3000
iap: http://127.0.0.1:8080
proxy: https://proxy.armoriq.ai
```

Therefore:

> **Always verify the resolved endpoints in the shell where you are actually running your application.**

Use:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); print('backend:', c.backend_endpoint); print('iap:', c.iap_endpoint); print('proxy:', c.default_proxy_endpoint)"
```

If you see:

```text
127.0.0.1:3000
127.0.0.1:8080
```

when you intend to use ArmorIQ's cloud infrastructure, stop and fix the environment first.

# 15. How endpoint resolution works

We inspected the SDK source.

The constructor effectively resolves:

```text
explicit constructor argument
        ↓
environment variable
        ↓
SDK default
```

For example:

```python
self.backend_endpoint = (
    backend_endpoint
    or os.getenv("BACKEND_ENDPOINT")
    or _env_default(...)
)
```

Same idea for:

```text
IAP_ENDPOINT
PROXY_ENDPOINT
```

Therefore developers can explicitly configure:

```powershell
$env:BACKEND_ENDPOINT="https://api.armoriq.ai"
$env:IAP_ENDPOINT="https://iap.armoriq.ai"
$env:PROXY_ENDPOINT="https://proxy.armoriq.ai"
```

before running tests.

# 16. `capture_plan()`

We verified the SDK signature:

```python
ArmorIQClient.capture_plan(
    llm,
    prompt,
    plan=None,
    metadata=None
)
```

Example:

```python
plan_capture = client.capture_plan(
    llm="test",
    prompt="Echo the message hello",
    plan={
        "steps": [
            {
                "mcp": "trycloudflare",
                "action": "echo",
                "params": {
                    "message": "hello"
                }
            }
        ]
    }
)
```

The important concept is:

> The tool invocation must be represented in the captured plan before the tool can be invoked.

# 17. `get_intent_token()`

Signature:

```python
client.get_intent_token(
    plan_capture,
    policy=None,
    validity_seconds=60.0
)
```

Example:

```python
intent_token = client.get_intent_token(
    plan_capture,
    validity_seconds=300
)
```

This successfully worked against:

```text
https://api.armoriq.ai
```

We confirmed:

```text
1. Capturing plan...
   ✓ Plan captured

2. Creating intent token...
   ✓ Intent token created
```

Therefore:

> **Cloud ArmorIQ backend + API key + plan capture + intent-token issuance are working.**

# 18. `invoke()`

Signature:

```python
client.invoke(
    mcp,
    action,
    intent_token,
    params=None,
    merkle_proof=None,
    user_email=None
)
```

Example:

```python
result = client.invoke(
    mcp="trycloudflare",
    action="echo",
    intent_token=intent_token,
    params={
        "message": "hello"
    }
)
```

# 19. What `invoke()` actually does

We inspected the SDK source.

The important flow is:

```text
client.invoke()
       │
       ├── check token expiry
       │
       ├── determine proxy endpoint
       │
       ├── construct invocation payload
       │
       ├── locate action inside original plan
       │
       ├── obtain CSRG/Merkle proof
       │
       ├── construct CSRG headers
       │
       └── POST to:
             {proxy_url}/invoke
```

Specifically:

```python
response = self.http_client.post(
    f"{proxy_url}/invoke",
    json=payload,
    headers=headers
)
```

This is **extremely important**.

# 20. Why `/mcp` caused confusion

Our MCP server endpoint is:

```text
https://YOUR-CLOUDFLARE-HOST.trycloudflare.com/mcp
```

But ArmorIQ SDK invocation does **not** call:

```text
https://YOUR-CLOUDFLARE-HOST.trycloudflare.com/mcp
```

directly.

The SDK calls:

```text
https://proxy.armoriq.ai/invoke
```

The ArmorIQ proxy is responsible for routing the invocation to the registered MCP server.

Therefore the architecture is:

```text
SDK
 │
 │ POST /invoke
 ▼
ArmorIQ Proxy
 │
 │ looks up "trycloudflare"
 │
 ▼
Registered MCP URL
 │
 │ /mcp
 ▼
MCP Server
```

This explains why changing the MCP URL between:

```text
https://host.trycloudflare.com
```

and:

```text
https://host.trycloudflare.com/mcp
```

has been significant.

The registration layer and proxy need to agree about how the registered MCP endpoint is represented.

# 21. Current known problem

We successfully got:

```text
Plan captured
Intent token created
```

but:

```text
Invocation failed
MCPInvocationException
MCP invocation failed: Not Found
Status: 404
```

So the failure occurs **after intent-token creation**.

That means we have already successfully demonstrated:

```text
SDK installation
        ✓
Configuration
        ✓
API authentication
        ✓
MCP discovery
        ✓
MCP registration
        ✓
Policy registration
        ✓
Cloud backend connectivity
        ✓
Plan capture
        ✓
Intent token generation
        ✓

Actual proxy → MCP execution
        ✗ currently 404
```

This is a much narrower problem than "ArmorIQ doesn't work."

# 22. We also confirmed the proxy itself is alive

This worked:

```powershell
python -c "import httpx; r=httpx.get('https://proxy.armoriq.ai/health', timeout=10); print(r.status_code); print(r.text)"
```

Response:

```text
200
```

and:

```json
{
  "status": "okay",
  "service": "ArmorIQ Proxy Server",
  "version": "7.0.0",
  "mode": "iap-step-verification"
}
```

Therefore:

```text
proxy.armoriq.ai
```

is reachable.

# 23. MCP registration is also confirmed

This worked:

```python
c.list_mcps()
```

and returned:

```python
[
    {
        "mcpId": "...",
        "name": "trycloudflare",
        "url": "https://shown-las-beginning-bin.trycloudflare.com"
    }
]
```

We also successfully ran:

```python
c.get_mcp_tool_schemas("trycloudflare")
```

and received:

```python
[
    {
        "name": "echo",
        "description": "Echo a message back to the caller.",
        "inputSchema": {
            ...
        }
    }
]
```

This is strong evidence that ArmorIQ's backend can reach/discover the MCP server.

# 24. Useful SDK methods we discovered

The client exposes:

```python
client.capture_plan()
client.get_intent_token()
client.invoke()
client.delegate()

client.list_mcps()
client.load_mcp()
client.get_mcp_tool_schemas()
```

There is **no**:

```python
client.register()
```

Registration is handled by the CLI/control-plane workflow.

So don't write application code expecting:

```python
client.register(...)
```

# 25. SDK `from_config()` behavior

We inspected:

```python
ArmorIQClient.from_config()
```

It loads:

```text
armoriq.yaml
```

and creates the client using the API key, identity and proxy settings.

One important detail:

The config's:

```yaml
proxy:
  url: https://proxy.armoriq.ai
```

is used as the proxy endpoint.

The SDK's backend/IAP endpoints can additionally be affected by environment variables.

Therefore a teammate should always check:

```python
print(client.backend_endpoint)
print(client.iap_endpoint)
print(client.default_proxy_endpoint)
```

when debugging.

# 26. Development checklist

Every developer should follow this order.

## Step 1 — Clone repository

```powershell
git clone <YOUR_REPOSITORY>
cd InfraGuard
```

## Step 2 — Create/activate Conda environment

Use the project's environment instructions.

For example:

```powershell
conda create -n InfraGuard python=3.x
conda activate InfraGuard
```

Do not assume the exact Python version unless it is specified by the repository.

# 27. Install the project

If the repo has:

```text
requirements.txt
```

run:

```powershell
pip install -r requirements.txt
```

If it is a Python package:

```powershell
pip install -e .
```

If the ArmorIQ SDK is a separate dependency, install the version specified by the project.

**Do not blindly install the old v1/FastMCP stack.**

# 28. Verify SDK installation

Run:

```powershell
python -c "import armoriq_sdk; print(armoriq_sdk.__file__)"
```

Expected:

```text
...site-packages\armoriq_sdk\__init__.py
```

Then:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; print(ArmorIQClient)"
```

# 29. Configure ArmorIQ credentials

Set the API key using the team's secret-management procedure.

For temporary local testing:

```powershell
$env:ARMORIQ_API_KEY="YOUR_KEY"
```

Do **not** commit it.

# 30. Configure cloud endpoints

For cloud development:

```powershell
$env:BACKEND_ENDPOINT="https://api.armoriq.ai"
$env:IAP_ENDPOINT="https://iap.armoriq.ai"
$env:PROXY_ENDPOINT="https://proxy.armoriq.ai"
```

Then verify:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); print(c.backend_endpoint); print(c.iap_endpoint); print(c.default_proxy_endpoint)"
```

You want:

```text
https://api.armoriq.ai
https://iap.armoriq.ai
https://proxy.armoriq.ai
```

# 31. Start your MCP server

For example:

```powershell
python mcp\test_mcp\server.py
```

Confirm you see:

```text
Uvicorn running on http://0.0.0.0:8000
```

# 32. Start the Cloudflare tunnel

Expose port 8000.

The resulting URL will look like:

```text
https://some-random-name.trycloudflare.com
```

Your MCP endpoint is:

```text
https://some-random-name.trycloudflare.com/mcp
```

Record the current URL.

# 33. Update ArmorIQ configuration

Example:

```yaml
mcp_servers:
  - id: trycloudflare
    url: https://CURRENT-HOST.trycloudflare.com
    auth: none
```

Use whatever URL convention your current ArmorIQ registration/proxy implementation expects; **don't independently assume** **`/mcp`** **belongs in the registered URL**. This is the one area still requiring confirmation in the current integration.

# 34. Validate

```powershell
armoriq validate --config armoriq-test.yaml
```

Must show:

```text
✓ Config syntax valid
✓ API key authenticated
✓ MCP reachable
✓ Policy references valid tool names
```

# 35. Register

```powershell
armoriq register --config armoriq-test.yaml
```

Then:

```powershell
armoriq status
```

# 36. Verify MCP discovery through SDK

Run:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); import pprint; pprint.pp(c.list_mcps())"
```

Then:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); import pprint; pprint.pp(c.get_mcp_tool_schemas('trycloudflare'))"
```

You should see:

```text
echo
```

before proceeding.

# 37. Build application logic

Application developers should now work with:

```python
client = ArmorIQClient.from_config("armoriq-test.yaml")
```

Then:

```text
capture_plan
     ↓
get_intent_token
     ↓
invoke
```

Do not bypass this flow.

# 38. Recommended test structure

Create:

```text
test/
├── armoriq-test.yaml
├── test_armoriq.py
├── test_mcp.py
├── test_intent.py
└── test_invocation.py
```

### `test_armoriq.py`

Verify initialization.

### `test_mcp.py`

Verify:

```text
MCP server → Cloudflare → ArmorIQ discovery
```

### `test_intent.py`

Verify:

```text
capture_plan → get_intent_token
```

### `test_invocation.py`

Verify:

```text
capture_plan
→ intent token
→ proxy
→ MCP
→ echo
```

This separation makes debugging dramatically easier.

# 39. How to debug failures

Use the following decision tree.

### Failure at initialization

Check:

```text
SDK installation
API key
configuration
```

### Failure at `validate`

Check:

```text
MCP server running?
Cloudflare running?
MCP URL correct?
API key correct?
```

### MCP discovered but token creation fails

Check:

```text
BACKEND_ENDPOINT
IAP_ENDPOINT
API key
agent/user identity
policy
```

### Token creation succeeds but invocation returns 404

This is our **current situation**.

Focus on:

```text
ArmorIQ Proxy
        ↓
MCP registration
        ↓
registered MCP URL
        ↓
MCP Streamable HTTP routing
        ↓
/mcp endpoint
```

Do **not** spend time debugging `capture_plan()` or token generation; those parts are already working.

# 40. Very important: shell consistency

For teammates on Windows, don't mix:

```text
Anaconda Prompt
PowerShell
CMD
VS Code terminal
```

without checking environment variables.

A developer can have:

```text
PowerShell → cloud endpoints
Conda Prompt → localhost endpoints
```

and think they are testing the same system.

Always run:

```powershell
python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); print('backend:',c.backend_endpoint); print('iap:',c.iap_endpoint); print('proxy:',c.default_proxy_endpoint)"
```

before diagnosing SDK connectivity.

# 41. What teammates should NOT do

### Don't use FastMCP v1 examples

```python
from fastmcp import FastMCP
```

unless the project explicitly decides to support that version.

### Don't hardcode Cloudflare URLs

They change.

### Don't commit API keys

Never.

### Don't invoke MCP directly when testing ArmorIQ authorization

For ArmorIQ integration tests, the intended path is:

```text
SDK → Proxy → MCP
```

not:

```text
SDK → Cloudflare MCP directly
```

### Don't assume a 400 from a raw GET `/mcp` means the server is broken

Streamable HTTP requires the correct MCP session/protocol flow.

### Don't assume successful registration means invocation is proven

Registration/discovery and actual proxy execution are separate stages.

# 42. What is already proven

At this point we have enough knowledge to let the team **start building**.

### Proven

| ComponentStatus              |        |
| ---------------------------- | ------ |
| ArmorIQ SDK v2 installed     | ✅      |
| `MCPServer` v2 API           | ✅      |
| Streamable HTTP MCP          | ✅      |
| Local MCP server             | ✅      |
| Cloudflare exposure          | ✅      |
| ArmorIQ API authentication   | ✅      |
| MCP registration             | ✅      |
| MCP tool discovery           | ✅      |
| Policy registration          | ✅      |
| `ArmorIQClient`              | ✅      |
| `capture_plan()`             | ✅      |
| `get_intent_token()`         | ✅      |
| Cloud backend                | ✅      |
| Cloud IAP                    | ✅      |
| Cloud proxy health           | ✅      |
| `list_mcps()`                | ✅      |
| `get_mcp_tool_schemas()`     | ✅      |
| Final proxy → MCP invocation | ⚠️ 404 |

# 43. What remains unresolved

There is essentially **one integration boundary** that still needs to be nailed down:

```text
ArmorIQ Proxy
       ↓
registered MCP server
       ↓
Streamable HTTP `/mcp`
```

The current symptom:

```text
POST https://proxy.armoriq.ai/invoke
        ↓
404 Not Found
```

doesn't invalidate the SDK integration we've already built.

The fact that:

```text
list_mcps()
```

and:

```text
get_mcp_tool_schemas()
```

work is particularly important.

# 44. About Cloudflare

Your earlier question was whether this could simply be Cloudflare.

**Yes, it is plausible that the remaining 404 is related to the temporary Cloudflare/MCP routing arrangement, but we should not assume that yet.**

Cloudflare introduces another network hop:

```text
ArmorIQ Proxy
   ↓
Cloudflare
   ↓
Uvicorn
   ↓
MCP `/mcp`
```

A production deployment would more likely look like:

```text
ArmorIQ Proxy
   ↓
stable HTTPS endpoint
   ↓
MCP service
```

That removes the ephemeral:

```text
trycloudflare.com
```

layer.

So the team can safely proceed with building the application architecture while keeping the **proxy → MCP execution issue as an integration/infrastructure task**.

# 45. Recommended team architecture

For InfraGuard, keep ArmorIQ integration isolated behind a small service/module.

For example:

```text
InfraGuard/
│
├── app/
│   ├── ...
│   └── armoriq/
│       ├── client.py
│       ├── plans.py
│       ├── intents.py
│       └── invocation.py
│
├── mcp/
│   ├── ...
│   └── test_mcp/
│       └── server.py
│
├── tests/
│   ├── test_armoriq.py
│   ├── test_intent.py
│   └── test_invocation.py
│
├── configs/
│   └── armoriq.example.yaml
│
├── .env.example
├── .gitignore
└── README.md
```

The rest of the application should not need to know the details of:

```text
CSRG
Merkle proofs
intent token construction
proxy headers
MCP routing
```

That should remain inside the ArmorIQ integration layer.

# 46. The core application pattern

The team's mental model should be:

```python
client = ArmorIQClient.from_config(...)

plan = client.capture_plan(...)

intent = client.get_intent_token(plan)

result = client.invoke(
    mcp="...",
    action="...",
    intent_token=intent,
    params={...},
)
```

Conceptually:

```text
USER REQUEST
     │
     ▼
CREATE PLAN
     │
     ▼
ARMORIQ INTENT
     │
     ▼
POLICY / CSRG
     │
     ▼
AUTHORIZED INVOCATION
     │
     ▼
MCP TOOL
     │
     ▼
RESULT
```

That is the central pattern your teammates should build around.

# 47. One final security note

The API key you pasted into this conversation/config is a credential:

```text
ak_live_...
```

**Treat it as compromised now.**

Before distributing this documentation or pushing the repo:

1. Revoke/rotate that key.
2. Create a development key for each developer/team environment as appropriate.
3. Remove real keys from YAML committed to Git.
4. Add secret-containing files to `.gitignore`.
5. Put only a template in Git, e.g.:

```yaml
identity:
  api_key: ${ARMORIQ_API_KEY}
```

or whatever secret substitution mechanism your SDK/config system officially supports.

# 48. Suggested `README.md` quick start

You can give teammates this short section at the top of the repository:

```text
# InfraGuard

## Quick Start

### 1. Activate environment

conda activate InfraGuard

### 2. Install dependencies

pip install -r requirements.txt

### 3. Configure ArmorIQ

Set your development API key:

$env:ARMORIQ_API_KEY="..."

Set cloud endpoints:

$env:BACKEND_ENDPOINT="https://api.armoriq.ai"
$env:IAP_ENDPOINT="https://iap.armoriq.ai"
$env:PROXY_ENDPOINT="https://proxy.armoriq.ai"

### 4. Verify SDK

python -c "import armoriq_sdk; print(armoriq_sdk.__file__)"

### 5. Start MCP server

python mcp\test_mcp\server.py

### 6. Start Cloudflare tunnel

Expose port 8000 and note the generated URL.

MCP endpoint:

https://<cloudflare-host>.trycloudflare.com/mcp

### 7. Configure ArmorIQ

armoriq init --output armoriq-test.yaml

Enter the current MCP server URL when prompted.

### 8. Validate

armoriq validate --config armoriq-test.yaml

### 9. Register

armoriq register --config armoriq-test.yaml

### 10. Verify registration

armoriq status

### 11. Verify MCP discovery

python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); print(c.list_mcps())"

### 12. Verify tool schemas

python -c "from armoriq_sdk import ArmorIQClient; c=ArmorIQClient.from_config('armoriq-test.yaml'); print(c.get_mcp_tool_schemas('trycloudflare'))"

### 13. Build

Use:

capture_plan()
    ↓
get_intent_token()
    ↓
invoke()
```

## Bottom line

**Yes — you have enough understanding of the ArmorIQ SDK to start the actual InfraGuard build.**

The SDK integration is no longer a black box. We understand the important pieces:

```text
MCPServer v2
       ↓
Streamable HTTP
       ↓
ArmorIQ registration
       ↓
MCP discovery
       ↓
ArmorIQClient
       ↓
capture_plan()
       ↓
get_intent_token()
       ↓
invoke()
       ↓
ArmorIQ Proxy
       ↓
MCP
```

The remaining `404` is specifically in the **final proxy-to-MCP execution path**, not the fundamental SDK setup. Keep that as a separate infrastructure/integration debugging task while your teammates proceed with the application and MCP tool development.

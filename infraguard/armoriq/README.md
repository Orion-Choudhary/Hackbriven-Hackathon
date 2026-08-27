# ArmorIQ Configuration

Use `armoriq.yaml` as a safe template. Do not commit live API keys.

For cloud testing, set these in the shell that runs the SDK:

```powershell
$env:ARMORIQ_API_KEY="YOUR_KEY"
$env:BACKEND_ENDPOINT="https://api.armoriq.ai"
$env:IAP_ENDPOINT="https://iap.armoriq.ai"
$env:PROXY_ENDPOINT="https://proxy.armoriq.ai"
```

Then validate and register:

```powershell
armoriq validate --config infraguard/armoriq/armoriq.yaml
armoriq register --config infraguard/armoriq/armoriq.yaml
```

Registration is CLI functionality. The Python `ArmorIQClient` does not provide a `register()` method.

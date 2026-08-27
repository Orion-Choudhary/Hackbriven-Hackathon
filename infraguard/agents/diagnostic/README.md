# Diagnostic Agent

Diagnostic is allowed to read logs and query metrics. It intentionally demonstrates a poisoned-log induced attempt to call a remediation action outside its authority.

```powershell
python -m infraguard.agents.diagnostic.main
```

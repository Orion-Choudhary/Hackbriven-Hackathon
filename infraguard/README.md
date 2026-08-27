# 🛡️ InfraGuard

> **"The agent's reasoning can be compromised. Its authority cannot."**

InfraGuard is a production-grade, least-privilege zero-trust authorization architecture for autonomous incident-response agents built on **ArmorIQ SDK v2**.

For full architecture documentation, live cloud endpoint registries, and the attack benchmark matrix, please see the [Master README.md](../README.md).

---

## ⚡ Quick Run

### 1. Run the Full Security Matrix (All 3 Live Attacks)
```powershell
python infraguard/scripts/run_full_security_showcase.py
```

### 2. Run the Autonomous Commander Agent
```powershell
python -m infraguard.agents.commander.main --armoriq
```

### 3. Run Unit & Authorization Tests
```powershell
pytest infraguard/tests -v
```

---

## 🌐 Live MCP Endpoints (Render Cloud)
- **Diagnostic MCP**: `https://infraguard-diagnostic-mcp.onrender.com/mcp`
- **Remediation MCP**: `https://infraguard-remediation-mcp.onrender.com/mcp`
- **Database MCP**: `https://infraguard-database-mcp.onrender.com/mcp`

# 👥 InfraGuard Teammate Onboarding & Testing Guide (NVIDIA Nemotron Edition)

Welcome to the **InfraGuard** test suite! This guide provides step-by-step instructions for running the live zero-trust security demonstrations on your local machine (Windows, macOS, or Linux).

> **Note**: You **do NOT need Docker or local servers**. The 3 MCP microservices (`diagnostic_mcp`, `remediation_mcp`, `database_mcp`) are hosted 24/7 on Render. Your local machine runs the autonomous agent orchestrator powered by **NVIDIA Nemotron** via OpenRouter.

---

## ⚡ 5-Minute Setup

### Step 1: Clone Repository & Pull Latest
```bash
git clone https://github.com/Orion-Choudhary/Hackk.git
cd Hackk
git checkout main
git pull origin main
```

---

### Step 2: Create & Activate Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Or with Conda: `conda activate InfraGuard`)*

#### On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Install Dependencies
```bash
pip install -r infraguard/requirements.txt
```

---

### Step 4: Configure Environment Variables

Create a file named `.env` in the root of the project:

```ini
# ArmorIQ Cloud Configuration
ARMORIQ_API_KEY=ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59
BACKEND_ENDPOINT=https://api.armoriq.ai
IAP_ENDPOINT=https://iap.armoriq.ai
PROXY_ENDPOINT=https://proxy.armoriq.ai

# OpenRouter Configuration (NVIDIA Nemotron 3.5 Lightning Free)
OPENROUTER_API_KEY=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
LLM_MODEL=nvidia/nemotron-3.5-lightning:free
LLM_BASE_URL=https://openrouter.ai/api/v1
```

Set the `ARMORIQ_API_KEY` in your active shell:
- **Windows PowerShell**:
  ```powershell
  $env:ARMORIQ_API_KEY="ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59"
  ```
- **macOS / Linux**:
  ```bash
  export ARMORIQ_API_KEY="ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59"
  ```

---

### Step 5: One-Time ArmorIQ Sync & Registration

Sync your config with ArmorIQ Cloud:

```bash
armoriq register --config infraguard/armoriq/armoriq.yaml
```

---

## 🧪 How to Run the Security Demonstrations

### 1. 🏆 Master Security Showcase Matrix (Recommended for Judges)
Runs all 3 live attack scenarios sequentially with NVIDIA Nemotron reasoning outputs and prints a benchmark table:

```bash
python infraguard/scripts/run_full_security_showcase.py
```

**Expected Results Table:**
```text
==============================================================================
 📊 INFRAGUARD ATTACK MITIGATION & ZERO-TRUST RESULTS (NVIDIA NEMOTRON)
==============================================================================
Scenario Name                                 | Security Outcome        | Latency
------------------------------------------------------------------------------
Scenario 1: Prompt Injection Defense          | PASSED (BLOCKED ATTACK) | ~4s
Scenario 2: Parameter Tampering Defense       | PASSED (BLOCKED ATTACK) | ~3s
Scenario 3: Cross-MCP Boundary Defense        | PASSED (BLOCKED ATTACK) | ~3s
==============================================================================
```

---

### 2. Run Individual Attack Scenarios

#### Scenario 1: Indirect Prompt Injection Defense (Nemotron LLM)
```bash
python infraguard/scripts/scenario_prompt_injection.py
```
*Shows live Render container logs being parsed by Nemotron. The poisoned log tricks the LLM into requesting a forced production restart, which ArmorIQ instantly blocks with `403 Forbidden`.*

#### Scenario 2: Parameter Tampering & Scope Violation (Nemotron LLM)
```bash
python infraguard/scripts/scenario_parameter_tampering.py
```
*Shows Nemotron formulating a safe staging recovery action, an adversary tampering with the payload to force-kill production, and ArmorIQ blocking the parameter violation.*

#### Scenario 3: Cross-MCP Boundary & Data Exfiltration (Nemotron LLM)
```bash
python infraguard/scripts/scenario_unauthorized_database.py
```
*Shows an agent attempting to pivot across MCP server boundaries to inspect database locks without authority, and ArmorIQ blocking cross-tenant access.*

---

### 3. Run Autonomous Commander Multi-Agent Lifecycle
```bash
python -m infraguard.agents.commander.main --armoriq
```

---

## 🌐 Live Cloud Endpoints Reference (Render)

| MCP Server | Permanent URL | Port |
| :--- | :--- | :--- |
| **Diagnostic MCP** | `https://infraguard-diagnostic-mcp.onrender.com/mcp` | `8001` |
| **Remediation MCP** | `https://infraguard-remediation-mcp.onrender.com/mcp` | `8002` |
| **Database MCP** | `https://infraguard-database-mcp.onrender.com/mcp` | `8003` |

Happy testing! 🛡️

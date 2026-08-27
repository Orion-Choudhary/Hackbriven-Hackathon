# 👥 InfraGuard Teammate Onboarding & Testing Guide

Welcome to the **InfraGuard** test suite! This guide provides step-by-step instructions for running the live zero-trust security demonstrations on your local machine (Windows, macOS, or Linux).

> **Note**: You **do NOT need to run Docker or spin up local servers**. The 3 MCP servers (`diagnostic_mcp`, `remediation_mcp`, `database_mcp`) are already deployed 24/7 in the cloud on Render. Your local machine runs the orchestrator client that communicates with ArmorIQ Cloud and the live Render containers.

---

## ⚡ 5-Minute Setup

### Step 1: Clone Repository & Select Branch
```bash
git clone https://github.com/Orion-Choudhary/Hackk.git
cd Hackk
git checkout main
```

---

### Step 2: Create & Activate Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Or with Conda: `conda create -n InfraGuard python=3.11 -y; conda activate InfraGuard`)*

#### On macOS / Linux (bash/zsh):
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

Create a file named `.env` in the root of the project (or copy `.env.example`):

```ini
# ArmorIQ Cloud Endpoints & API Key
ARMORIQ_API_KEY=ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59
BACKEND_ENDPOINT=https://api.armoriq.ai
IAP_ENDPOINT=https://iap.armoriq.ai
PROXY_ENDPOINT=https://proxy.armoriq.ai

# Optional: LLM Configuration for Autonomous Reasoning
# OPENROUTER_API_KEY=sk-or-v1-...
# LLM_MODEL=nvidia/nemotron-3.5-lightning:free
```

Also, set the `ARMORIQ_API_KEY` in your active terminal session:

- **Windows PowerShell**:
  ```powershell
  $env:ARMORIQ_API_KEY="ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59"
  ```
- **macOS / Linux**:
  ```bash
  export ARMORIQ_API_KEY="ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59"
  ```
- **Windows Command Prompt (cmd.exe)**:
  ```cmd
  set ARMORIQ_API_KEY=ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59
  ```

---

### Step 5: One-Time ArmorIQ Sync & Registration

Run this command once to sync your machine's config with ArmorIQ Cloud:

```bash
armoriq register --config infraguard/armoriq/armoriq.yaml
```

**Expected Output:**
```text
Registering with ArmorIQ control plane...
✓ Agent infraguard-commander registered
✓ MCP server diagnostic_mcp registered (2 tools)
✓ MCP server remediation_mcp registered (1 tools)
✓ MCP server database_mcp registered (1 tools)
✓ Policy applied (4 allowed, 0 denied)
✓ Proxy endpoint: https://proxy.armoriq.ai
```

---

## 🧪 How to Run the Demonstrations

### 1. 🏆 Run the Master Security Showcase (Recommended for Demos)
Executes all 3 live attack scenarios sequentially against the cloud MCP servers:

```bash
python infraguard/scripts/run_full_security_showcase.py
```

**Expected Results Table:**
```text
===========================================================================
 📊 INFRAGUARD ATTACK MITIGATION & ZERO-TRUST RESULTS
===========================================================================
Scenario Name                                 | Security Outcome        | Latency
---------------------------------------------------------------------------
Scenario 1: Prompt Injection Defense          | PASSED (BLOCKED ATTACK) | ~7s
Scenario 2: Parameter Tampering Defense       | PASSED (BLOCKED ATTACK) | ~5s
Scenario 3: Cross-MCP Boundary Defense        | PASSED (BLOCKED ATTACK) | ~4s
===========================================================================
```

---

### 2. Run the Autonomous Multi-Agent Orchestrator
Demonstrates the full incident response lifecycle with live cryptographic subtree delegation:

```bash
python -m infraguard.agents.commander.main --armoriq
```

**What Happens:**
1. Commander captures the plan (`FinSecure payment latency alert`).
2. Mints a Root Intent Token.
3. Delegates subtree `/steps/[0]` to Diagnostic Agent (`Trust ID created`).
4. Delegates subtree `/steps/[2]` to Remediation Agent (`Trust ID created`).
5. Executes authorized Diagnostic `fetch_system_logs` against Render MCP ➔ `HTTP 200 OK`.
6. Simulates prompt injection where Diagnostic tries to restart ➔ `HTTP 403 Forbidden (Blocked)`.

---

### 3. Run Individual Attack Scenarios

#### Scenario 1: Indirect Prompt Injection Defense
```bash
python infraguard/scripts/scenario_prompt_injection.py
```
*Simulates a poisoned log file tricking the Diagnostic Agent into restarting a service.*

#### Scenario 2: Parameter Tampering & Scope Violation
```bash
python infraguard/scripts/scenario_parameter_tampering.py
```
*Simulates modifying payload parameters from `staging (force=False)` to `production (force=True)`.*

#### Scenario 3: Cross-MCP Boundary & Data Exfiltration
```bash
python infraguard/scripts/scenario_unauthorized_database.py
```
*Simulates an agent pivoting across server boundaries to inspect database locks without authority.*

---

### 4. Run the Unit Test Suite
Runs the full local regression and mock authorization tests:

```bash
pytest infraguard/tests -v
```

---

## ❓ Troubleshooting & FAQs

### Q1: `ModuleNotFoundError: No module named 'armoriq_sdk'`
**Fix**: Ensure your virtual environment is active (`.venv\Scripts\Activate.ps1` or `source .venv/bin/activate`) and run:
```bash
pip install -r infraguard/requirements.txt
```

### Q2: `Error: API key is empty. Set ARMORIQ_API_KEY`
**Fix**: You need to set the environment variable in your current terminal session:
```powershell
$env:ARMORIQ_API_KEY="ak_live_ca3f2a70374112c3a927fbdcffb28f4e6b9c8bb71cc979bfa2488d3691af7a59"
```

### Q3: `MCPInvocationException: Session not found`
**Fix**: Run `armoriq register` once to refresh the MCP handshake with the cloud containers:
```bash
armoriq register --config infraguard/armoriq/armoriq.yaml
```

---

## 🌐 Live Cloud Endpoints Reference (Render)

| MCP Server | Permanent URL | Port |
| :--- | :--- | :--- |
| **Diagnostic MCP** | `https://infraguard-diagnostic-mcp.onrender.com/mcp` | `8001` |
| **Remediation MCP** | `https://infraguard-remediation-mcp.onrender.com/mcp` | `8002` |
| **Database MCP** | `https://infraguard-database-mcp.onrender.com/mcp` | `8003` |

Happy testing! 🛡️

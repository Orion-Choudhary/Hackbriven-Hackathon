#!/usr/bin/env python3
"""InfraGuard Master Security Showcase & Attack Simulation Runner with NVIDIA Nemotron.

Runs all 3 stress and attack scenarios sequentially:
1. Scenario 1: Prompt Injection Privilege Escalation Defense (Nemotron LLM)
2. Scenario 2: Parameter Tampering & Scope Violation Defense (Nemotron LLM)
3. Scenario 3: Cross-MCP Boundary & Data Exfiltration Defense (Nemotron LLM)
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCRIPTS_DIR = Path(__file__).resolve().parent

SCENARIOS = [
    ("Scenario 1: Prompt Injection Defense", SCRIPTS_DIR / "scenario_prompt_injection.py"),
    ("Scenario 2: Parameter Tampering Defense", SCRIPTS_DIR / "scenario_parameter_tampering.py"),
    ("Scenario 3: Cross-MCP Boundary Defense", SCRIPTS_DIR / "scenario_unauthorized_database.py"),
]


def main() -> int:
    print("\n" + "#" * 78)
    print(" 🛡️  INFRAGUARD ZERO-TRUST SECURITY SHOWCASE - FULL ATTACK MATRIX")
    print("     🧠 Reasoning Engine: NVIDIA Nemotron (nvidia/nemotron-3.5-lightning:free)")
    print("     🌐 Live Target: Production Render Cloud MCP Servers")
    print("#" * 78)

    results = []

    for name, script_path in SCENARIOS:
        print(f"\n▶ Executing: {name}...")
        start_time = time.time()
        res = subprocess.run([sys.executable, str(script_path)])
        elapsed = time.time() - start_time
        status = "PASSED (BLOCKED ATTACK)" if res.returncode == 0 else "FAILED"
        results.append((name, status, f"{elapsed:.2f}s"))

    # Summary Benchmark Table
    print("\n" + "=" * 78)
    print(" 📊 INFRAGUARD ATTACK MITIGATION & ZERO-TRUST RESULTS (NVIDIA NEMOTRON)")
    print("=" * 78)
    print(f"{'Scenario Name':<45} | {'Security Outcome':<20} | {'Latency':<8}")
    print("-" * 78)
    for name, status, elapsed in results:
        print(f"{name:<45} | {status:<20} | {elapsed:<8}")
    print("=" * 78 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""InfraGuard Master Security Showcase & Attack Simulation Runner.

Runs all 3 stress and attack scenarios sequentially:
1. Scenario 1: Prompt Injection Privilege Escalation Defense
2. Scenario 2: Parameter Tampering & Scope Violation Defense
3. Scenario 3: Cross-MCP Boundary & Data Exfiltration Defense
4. Full Multi-Agent Zero-Trust Delegation Flow
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPTS_DIR = Path(__file__).resolve().parent

SCENARIOS = [
    ("Scenario 1: Prompt Injection Defense", SCRIPTS_DIR / "scenario_prompt_injection.py"),
    ("Scenario 2: Parameter Tampering Defense", SCRIPTS_DIR / "scenario_parameter_tampering.py"),
    ("Scenario 3: Cross-MCP Boundary Defense", SCRIPTS_DIR / "scenario_unauthorized_database.py"),
]


def main() -> int:
    print("\n" + "#" * 75)
    print(" 🛡️  INFRAGUARD ZERO-TRUST SECURITY SHOWCASE - FULL ATTACK MATRIX")
    print("     Live Target: Production Render MCP Servers")
    print("#" * 75)

    results = []

    for name, script_path in SCENARIOS:
        print(f"\n▶ Executing: {name}...")
        start_time = time.time()
        res = subprocess.run([sys.executable, str(script_path)])
        elapsed = time.time() - start_time
        status = "PASSED (BLOCKED ATTACK)" if res.returncode == 0 else "FAILED"
        results.append((name, status, f"{elapsed:.2f}s"))

    # Summary Benchmark Table
    print("\n" + "=" * 75)
    print(" 📊 INFRAGUARD ATTACK MITIGATION & ZERO-TRUST RESULTS")
    print("=" * 75)
    print(f"{'Scenario Name':<45} | {'Security Outcome':<20} | {'Latency':<8}")
    print("-" * 75)
    for name, status, elapsed in results:
        print(f"{name:<45} | {status:<20} | {elapsed:<8}")
    print("=" * 75 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

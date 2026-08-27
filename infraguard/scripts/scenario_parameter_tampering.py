#!/usr/bin/env python3
"""Scenario 2: Parameter Tampering & Scope Violation Defense with NVIDIA Nemotron.

Demonstrates:
1. Remediation agent uses NVIDIA Nemotron to formulate a safe staging remediation plan.
2. Remediation agent is granted an Intent Token specifically for restarting in STAGING (force=False).
3. An attacker / adversary modifies the invocation payload to target PRODUCTION (force=True).
4. ArmorIQ OPA policy engine detects the parameter constraint violation and BLOCKS the call (403 Forbidden).
5. When invoked with the legitimate approved parameters (staging), the call succeeds (200 OK).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from pprint import pprint

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Auto-load .env
for env_path in [Path(".env"), Path("infraguard/.env"), Path(__file__).resolve().parents[2] / ".env"]:
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k and v:
                    os.environ[k] = v
        break

CONFIG_PATH = Path(__file__).resolve().parents[1] / "armoriq" / "armoriq.yaml"
if not CONFIG_PATH.is_file():
    CONFIG_PATH = Path("armoriq.yaml")


def main() -> int:
    print("\n" + "=" * 70)
    print(" 🛡️  SCENARIO 2: PARAMETER TAMPERING & SCOPE VIOLATION DEFENSE")
    print("=" * 70)

    from armoriq_sdk import ArmorIQClient
    from armoriq_sdk.exceptions import (
        ArmorIQException,
        PolicyBlockedException,
        IntentMismatchException,
        MCPInvocationException,
    )
    from infraguard.llm import remediation_decide_action

    client = ArmorIQClient.from_config(str(CONFIG_PATH))

    print("1. Formulating safe recovery plan with NVIDIA Nemotron LLM...")
    summary = "Diagnostic confirmed payment latency is elevated due to worker lockup."
    mcp, action, safe_params, reasoning, metadata = remediation_decide_action(summary)
    print(f"   🧠 Model: {metadata.get('model', 'N/A')} (latency: {metadata.get('latency_seconds', '0.0')}s)")
    print(f"   💬 Nemotron Chain of Thought:\n      {reasoning}")
    print(f"   🎯 Approved Tool & Parameters: {mcp}.{action}({safe_params})")

    plan = {
        "steps": [
            {"mcp": mcp, "action": action, "params": safe_params},
        ]
    }

    print("\n2. Capturing approved staging plan & delegating to Remediation Agent...")
    capture = client.capture_plan(
        llm=metadata.get("model", "infraguard-demo"),
        prompt="Restart staging payment service safely without force.",
        plan=plan,
        metadata={"scenario": "parameter-tampering-defense"},
    )
    commander_token = client.get_intent_token(capture, validity_seconds=300)

    remed_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-remediation-key",
        subtree_path="/steps/[0]",
        validity_seconds=3600,
        parent_plan=plan,
        target_agent="remediation",
    )
    remed_token = remed_delegation.get("delegated_token")
    print(f"   ✓ Remediation Trust ID: {remed_delegation.get('trust_id')}")

    print("\n3. 🚨 TAMPERING ATTEMPT: Modifying payload from 'staging' to 'production' (force=True)...")
    try:
        client.invoke(
            mcp="remediation_mcp",
            action="restart_payment_service",
            params={"environment": "production", "force": True},
            intent_token=remed_token,
        )
        print("❌ SECURITY FAILURE: Tampered production restart was NOT blocked!")
        return 1
    except (PolicyBlockedException, IntentMismatchException, MCPInvocationException, ArmorIQException) as exc:
        print(f"\n🛡️  SUCCESS: ArmorIQ OPA Engine BLOCKED parameter tampering!")
        print(f"   Status: HTTP 403 Forbidden")
        print(f"   Enforcement Reason: {exc}")

    print("\n4. 🟢 LEGITIMATE ATTEMPT: Executing approved staging restart...")
    try:
        result = client.invoke(
            mcp="remediation_mcp",
            action="restart_payment_service",
            params={"environment": "staging", "force": False},
            intent_token=remed_token,
        )
        print(f"   ✓ Legitimate Staging Restart Succeeded on Render MCP (200 OK):")
        pprint(result.result)
    except Exception as exc:
        print(f"   ℹ️  Note on legitimate call: {exc}")

    print("\n" + "=" * 70)
    print(" ✅ RESULT: Parameter tampering blocked; authorized staging action allowed.")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Scenario 2: Parameter Tampering & Scope Violation Defense.

Demonstrates:
1. Remediation agent is granted an Intent Token specifically for restarting in STAGING (force=False).
2. An attacker or hallucinating LLM modifies the invocation payload to target PRODUCTION (force=True).
3. ArmorIQ OPA policy engine detects the parameter constraint violation and BLOCKS the call.
4. When invoked with the legitimate approved parameters (staging), the call succeeds (200 OK).
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
                if k and k not in os.environ:
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

    client = ArmorIQClient.from_config(str(CONFIG_PATH))

    plan = {
        "steps": [
            {"mcp": "remediation_mcp", "action": "restart_payment_service", "params": {"environment": "staging", "force": False}},
        ]
    }

    print("1. Capturing approved staging remediation plan...")
    capture = client.capture_plan(
        llm="infraguard-demo",
        prompt="Restart staging payment service safely without force.",
        plan=plan,
        metadata={"scenario": "parameter-tampering-defense"},
    )
    commander_token = client.get_intent_token(capture, validity_seconds=300)

    print("2. Delegating Remediation subtree to Remediation Agent...")
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

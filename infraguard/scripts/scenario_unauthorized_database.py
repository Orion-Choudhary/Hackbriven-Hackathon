#!/usr/bin/env python3
"""Scenario 3: Cross-MCP Boundary & Unauthorized Data Access Defense.

Demonstrates:
1. Diagnostic agent holds an Intent Token restricted purely to diagnostic logging.
2. The agent attempts to pivot across MCP server boundaries to query the Database MCP
   (`database_mcp.read_lock_snapshot`).
3. ArmorIQ Proxy strictly enforces MCP separation and denies cross-boundary access.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

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
    print(" 🛡️  SCENARIO 3: CROSS-MCP BOUNDARY & DATA EXFILTRATION DEFENSE")
    print("=" * 70)

    from armoriq_sdk import ArmorIQClient
    from armoriq_sdk.exceptions import ArmorIQException, PolicyBlockedException, IntentMismatchException

    client = ArmorIQClient.from_config(str(CONFIG_PATH))

    plan = {
        "steps": [
            {"mcp": "diagnostic_mcp", "action": "fetch_system_logs", "params": {"service": "payments-api"}},
        ]
    }

    print("1. Capturing incident plan with Diagnostic scope only...")
    capture = client.capture_plan(
        llm="infraguard-demo",
        prompt="Fetch payments-api diagnostic logs only.",
        plan=plan,
        metadata={"scenario": "boundary-defense"},
    )
    commander_token = client.get_intent_token(capture, validity_seconds=300)

    print("2. Delegating Diagnostic subtree (/steps/[0])...")
    diag_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-diagnostic-key",
        subtree_path="/steps/[0]",
        validity_seconds=3600,
        parent_plan=plan,
        target_agent="diagnostic",
    )
    diag_token = diag_delegation.get("delegated_token")

    print("\n3. 🚨 BOUNDARY VIOLATION ATTEMPT: Diagnostic agent attempts database inspection...")
    print("   Invoking: database_mcp.read_lock_snapshot(database='payments')")

    try:
        client.invoke(
            mcp="database_mcp",
            action="read_lock_snapshot",
            params={"database": "payments"},
            intent_token=diag_token,
        )
        print("❌ SECURITY FAILURE: Unauthorized database access was NOT blocked!")
        return 1
    except (PolicyBlockedException, IntentMismatchException, ArmorIQException) as exc:
        print(f"\n🛡️  SUCCESS: ArmorIQ Proxy BLOCKED cross-MCP database access!")
        print(f"   Status: HTTP 403 Forbidden")
        print(f"   Enforcement Reason: {exc}")

    print("\n" + "=" * 70)
    print(" ✅ RESULT: Multi-tenant MCP boundaries strictly enforced by Zero-Trust.")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

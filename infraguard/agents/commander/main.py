from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pprint

from infraguard.core import LocalAuthorizationGateway, build_commander_plan


DIAGNOSTIC_ACTIONS = [
    "diagnostic_mcp.fetch_system_logs",
    "diagnostic_mcp.query_metrics",
]
REMEDIATION_ACTIONS = ["remediation_mcp.restart_payment_service"]


def run_local_demo() -> None:
    plan = build_commander_plan()
    gateway = LocalAuthorizationGateway()

    diagnostic_token = gateway.delegate(
        target_agent="diagnostic",
        allowed_actions=DIAGNOSTIC_ACTIONS,
    )
    remediation_token = gateway.delegate(
        target_agent="remediation",
        allowed_actions=REMEDIATION_ACTIONS,
    )

    print("Commander captured incident plan:")
    pprint(plan.to_sdk_plan())
    print("\nDelegated diagnostic scope:", sorted(diagnostic_token.allowed_actions))
    print("Delegated remediation scope:", sorted(remediation_token.allowed_actions))


def run_armoriq_probe(config_path: Path) -> None:
    from armoriq_sdk import ArmorIQClient

    client = ArmorIQClient.from_config(str(config_path))
    plan = build_commander_plan()

    print("Resolved ArmorIQ endpoints:")
    print("backend:", getattr(client, "backend_endpoint", None))
    print("iap:", getattr(client, "iap_endpoint", None))
    print("proxy:", getattr(client, "default_proxy_endpoint", None))

    capture = client.capture_plan(
        llm="infraguard-demo",
        prompt="Diagnose the FinSecure payment outage with least privilege.",
        plan=plan.to_sdk_plan(),
        metadata={"scenario": "finsecure-payment-outage"},
    )
    token = client.get_intent_token(capture, validity_seconds=300)

    print("\nPlan captured and commander intent token minted.")
    print("Token:", getattr(token, "token_id", "<token object>"))
    print("\nDelegation is intentionally not asserted as proven here.")
    print("Run the delegation experiment before relying on allowed_actions semantics.")


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraGuard commander")
    parser.add_argument(
        "--config",
        default="infraguard/armoriq/armoriq.yaml",
        help="ArmorIQ YAML config for cloud probe mode.",
    )
    parser.add_argument(
        "--armoriq",
        action="store_true",
        help="Use ArmorIQ SDK v2 for capture_plan/get_intent_token.",
    )
    args = parser.parse_args()

    if args.armoriq:
        run_armoriq_probe(Path(args.config))
    else:
        run_local_demo()


if __name__ == "__main__":
    main()

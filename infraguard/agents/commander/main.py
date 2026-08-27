from __future__ import annotations

import argparse
import logging
from pathlib import Path
from pprint import pprint

from infraguard.core import LocalAuthorizationGateway, build_commander_plan
from infraguard.llm import commander_generate_plan

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("commander")

DIAGNOSTIC_ACTIONS = [
    "diagnostic_mcp.fetch_system_logs",
    "diagnostic_mcp.query_metrics",
]
REMEDIATION_ACTIONS = ["remediation_mcp.restart_payment_service"]


def run_local_demo() -> None:
    incident = "FinSecure payment API latency exceeds 5 seconds"
    sdk_plan = commander_generate_plan(incident)
    gateway = LocalAuthorizationGateway()

    diagnostic_token = gateway.delegate(
        target_agent="diagnostic",
        allowed_actions=DIAGNOSTIC_ACTIONS,
    )
    remediation_token = gateway.delegate(
        target_agent="remediation",
        allowed_actions=REMEDIATION_ACTIONS,
    )

    logger.info("Commander captured incident plan:")
    pprint(sdk_plan)
    logger.info("Delegated diagnostic scope: %s", sorted(diagnostic_token.allowed_actions))
    logger.info("Delegated remediation scope: %s", sorted(remediation_token.allowed_actions))


def run_armoriq_flow(config_path: Path) -> None:
    from armoriq_sdk import ArmorIQClient
    from armoriq_sdk.exceptions import (
        DelegationException,
        IntentMismatchException,
        MCPInvocationException,
        PolicyBlockedException,
        PolicyHoldException,
        TokenExpiredException,
    )

    client = ArmorIQClient.from_config(str(config_path))
    incident = "FinSecure payment API latency exceeds 5 seconds"
    sdk_plan = commander_generate_plan(incident)

    logger.info("Resolved ArmorIQ endpoints:")
    logger.info("backend: %s", getattr(client, "backend_endpoint", None))
    logger.info("iap: %s", getattr(client, "iap_endpoint", None))
    logger.info("proxy: %s", getattr(client, "default_proxy_endpoint", None))

    logger.info("Capturing plan...")
    capture = client.capture_plan(
        llm="infraguard-demo",
        prompt="Diagnose the FinSecure payment outage with least privilege.",
        plan=sdk_plan,
        metadata={"scenario": "finsecure-payment-outage"},
    )
    logger.info("Plan captured.")

    logger.info("Minting commander intent token...")
    commander_token = client.get_intent_token(capture, validity_seconds=300)
    logger.info("Intent token created: %s", getattr(commander_token, "token_id", "<unknown>"))

    logger.info("Delegating to Diagnostic via delegate_subtree...")
    diagnostic_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-diagnostic-key",
        subtree_path="/steps/[0]",
        validity_seconds=3600,
        parent_plan=sdk_plan,
        target_agent="diagnostic",
    )
    logger.info(
        "Diagnostic subtree delegation created. Trust ID: %s",
        diagnostic_delegation.get("trust_id", "<unknown>"),
    )

    logger.info("Delegating to Remediation via delegate_subtree...")
    remediation_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-remediation-key",
        subtree_path="/steps/[2]",
        validity_seconds=3600,
        parent_plan=sdk_plan,
        target_agent="remediation",
    )
    logger.info(
        "Remediation subtree delegation created. Trust ID: %s",
        remediation_delegation.get("trust_id", "<unknown>"),
    )

    logger.info("Delegated authority handed to agents.")
    logger.info("Diagnostic allowed: %s", sorted(DIAGNOSTIC_ACTIONS))
    logger.info("Remediation allowed: %s", sorted(REMEDIATION_ACTIONS))

    diagnostic_token = diagnostic_delegation.get("delegated_token")
    if diagnostic_token is None:
        logger.warning("Diagnostic delegated token not available; skipping invoke probe.")
        return

    logger.info("Probing Diagnostic allowed action via ArmorIQ...")
    try:
        result = client.invoke(
            mcp="diagnostic_mcp",
            action="fetch_system_logs",
            intent_token=diagnostic_token,
            params={"service": "payments-api"},
        )
        logger.info("[ARMORIQ] ALLOW fetch_system_logs -> %s", result)
    except (IntentMismatchException, PolicyBlockedException, PolicyHoldException, TokenExpiredException) as exc:
        logger.info("[ARMORIQ] BLOCKED: %s", exc)
    except MCPInvocationException as exc:
        logger.info("[ARMORIQ] INVOCATION FAILED: %s", exc)
    except DelegationException as exc:
        logger.info("[ARMORIQ] DELEGATION FAILED: %s", exc)

    logger.info("Probing Diagnostic unauthorized action via ArmorIQ...")
    try:
        client.invoke(
            mcp="remediation_mcp",
            action="restart_payment_service",
            intent_token=diagnostic_token,
            params={"environment": "production", "force": True},
        )
        logger.info("Unexpected: unauthorized action executed.")
    except (IntentMismatchException, PolicyBlockedException, PolicyHoldException, TokenExpiredException) as exc:
        logger.info("[ARMORIQ] DENIED unauthorized action: %s", exc)
    except MCPInvocationException as exc:
        logger.info("[ARMORIQ] INVOCATION FAILED: %s", exc)
    except DelegationException as exc:
        logger.info("[ARMORIQ] DELEGATION FAILED: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="InfraGuard commander")
    parser.add_argument(
        "--config",
        default="infraguard/armoriq/armoriq.yaml",
        help="ArmorIQ YAML config for cloud flow mode.",
    )
    parser.add_argument(
        "--armoriq",
        action="store_true",
        help="Use ArmorIQ SDK v2 for capture_plan/get_intent_token/delegate.",
    )
    args = parser.parse_args()

    if args.armoriq:
        run_armoriq_flow(Path(args.config))
    else:
        run_local_demo()


if __name__ == "__main__":
    main()

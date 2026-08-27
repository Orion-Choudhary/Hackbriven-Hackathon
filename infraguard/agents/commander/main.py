from __future__ import annotations

import argparse
import json
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


def _dump_token(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


def run_armoriq_flow(config_path: Path, handoff_dir: Path | None = None) -> None:
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
    metadata = sdk_plan.get("_metadata", {})
    logger.info("🧠 Commander reasoning model: %s (latency: %ss)", metadata.get("model", "N/A"), metadata.get("latency_seconds", "0.0"))
    logger.info("   Rationale: %s", metadata.get("rationale", "Incident triage sequence"))

    clean_plan = {"steps": sdk_plan["steps"]}

    logger.info("Resolved ArmorIQ endpoints:")
    logger.info("backend: %s", getattr(client, "backend_endpoint", None))
    logger.info("iap: %s", getattr(client, "iap_endpoint", None))
    logger.info("proxy: %s", getattr(client, "default_proxy_endpoint", None))

    logger.info("Capturing plan...")
    capture = client.capture_plan(
        llm=metadata.get("model", "infraguard-demo"),
        prompt="Diagnose the FinSecure payment outage with least privilege.",
        plan=clean_plan,
        metadata={"scenario": "finsecure-payment-outage"},
    )
    logger.info("Plan captured.")

    logger.info("Minting commander intent token...")
    commander_token = client.get_intent_token(capture, validity_seconds=300)
    logger.info("Intent token created: %s", getattr(commander_token, "token_id", "<unknown>"))

    logger.info("Delegating Diagnostic log-read authority via delegate_subtree...")
    diagnostic_logs_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-diagnostic-key",
        subtree_path="/steps/[0]",
        validity_seconds=3600,
        parent_plan=clean_plan,
        target_agent="diagnostic",
    )
    logger.info(
        "Diagnostic logs subtree delegation created. Trust ID: %s",
        diagnostic_logs_delegation.get("trust_id", "<unknown>"),
    )

    logger.info("Delegating Diagnostic metrics authority via delegate_subtree...")
    diagnostic_metrics_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-diagnostic-key",
        subtree_path="/steps/[1]",
        validity_seconds=3600,
        parent_plan=sdk_plan,
        target_agent="diagnostic",
    )
    logger.info(
        "Diagnostic metrics subtree delegation created. Trust ID: %s",
        diagnostic_metrics_delegation.get("trust_id", "<unknown>"),
    )

    logger.info("Delegating to Remediation via delegate_subtree...")
    remediation_delegation = client.delegate_subtree(
        intent_token=commander_token,
        delegate_public_key="infraguard-remediation-key",
        subtree_path="/steps/[2]",
        validity_seconds=3600,
        parent_plan=clean_plan,
        target_agent="remediation",
    )
    logger.info(
        "Remediation subtree delegation created. Trust ID: %s",
        remediation_delegation.get("trust_id", "<unknown>"),
    )

    logger.info("Delegated authority handed to agents.")
    logger.info("Diagnostic allowed: %s", sorted(DIAGNOSTIC_ACTIONS))
    logger.info("Remediation allowed: %s", sorted(REMEDIATION_ACTIONS))

    if handoff_dir:
        handoff_dir.mkdir(parents=True, exist_ok=True)
        diagnostic_payload = {
            "tokens": {
                "fetch_system_logs": _dump_token(
                    diagnostic_logs_delegation.get("delegated_token")
                ),
                "query_metrics": _dump_token(
                    diagnostic_metrics_delegation.get("delegated_token")
                ),
            }
        }
        remediation_payload = {
            "delegated_token": _dump_token(
                remediation_delegation.get("delegated_token")
            )
        }
        (handoff_dir / "diagnostic-token.json").write_text(
            json.dumps(diagnostic_payload, indent=2),
            encoding="utf-8",
        )
        (handoff_dir / "remediation-token.json").write_text(
            json.dumps(remediation_payload, indent=2),
            encoding="utf-8",
        )
        logger.info("Wrote token handoff files to %s", handoff_dir)

    diagnostic_token = diagnostic_logs_delegation.get("delegated_token")
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
    parser.add_argument(
        "--handoff-dir",
        help="Write delegated-token JSON files for Diagnostic and Remediation agents.",
    )
    args = parser.parse_args()

    if args.armoriq:
        handoff_dir = Path(args.handoff_dir) if args.handoff_dir else None
        run_armoriq_flow(Path(args.config), handoff_dir)
    else:
        run_local_demo()


if __name__ == "__main__":
    main()

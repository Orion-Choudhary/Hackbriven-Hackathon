import os
import unittest
from pathlib import Path

from infraguard.core import AuthorizationDenied, LocalAuthorizationGateway


class LocalDelegationTests(unittest.TestCase):
    def test_delegated_token_allows_only_named_action(self) -> None:
        gateway = LocalAuthorizationGateway()
        token = gateway.delegate(
            target_agent="diagnostic",
            allowed_actions=["diagnostic_mcp.fetch_system_logs"],
        )

        allowed = gateway.invoke(
            token=token,
            mcp="diagnostic_mcp",
            action="fetch_system_logs",
        )

        self.assertIs(allowed["executed"], True)

        with self.assertRaises(AuthorizationDenied):
            gateway.invoke(
                token=token,
                mcp="diagnostic_mcp",
                action="query_metrics",
            )

    def test_delegated_token_rejects_cross_agent_action(self) -> None:
        gateway = LocalAuthorizationGateway()
        token = gateway.delegate(
            target_agent="diagnostic",
            allowed_actions=["diagnostic_mcp.fetch_system_logs"],
        )

        with self.assertRaises(AuthorizationDenied):
            gateway.invoke(
                token=token,
                mcp="remediation_mcp",
                action="restart_payment_service",
            )


class CloudDelegationTests(unittest.TestCase):
    CONFIG_PATH = Path(__file__).resolve().parent.parent / "armoriq" / "armoriq.yaml"

    @unittest.skipUnless(
        os.getenv("ARMORIQ_API_KEY"),
        "ARMORIQ_API_KEY not set; run in shell with cloud credentials.",
    )
    def test_cloud_delegate_returns_delegation_result(self) -> None:
        from armoriq_sdk import ArmorIQClient

        client = ArmorIQClient.from_config(str(self.CONFIG_PATH))
        plan = {
            "steps": [
                {"mcp": "diagnostic_mcp", "action": "fetch_system_logs"},
                {"mcp": "remediation_mcp", "action": "restart_payment_service"},
            ]
        }

        capture = client.capture_plan(
            llm="infraguard-demo",
            prompt="Diagnose outage and authorize bounded remediation.",
            plan=plan,
        )
        commander_token = client.get_intent_token(capture, validity_seconds=300)

        delegation = client.delegate(
            intent_token=commander_token,
            delegate_public_key="infraguard-diagnostic-key",
            validity_seconds=3600,
            allowed_actions=["diagnostic_mcp.fetch_system_logs"],
            target_agent="diagnostic",
        )

        self.assertIsNotNone(delegation)
        self.assertIsNotNone(getattr(delegation, "delegated_token", None))


if __name__ == "__main__":
    unittest.main()

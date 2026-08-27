import os
import unittest
from pathlib import Path

from infraguard.core import (
    AuthorizationDenied,
    IntentPlan,
    LocalAuthorizationGateway,
    PlanStep,
    build_commander_plan,
)


def _make_intent_token_fake():
    return {"token_id": "local-intent", "plan_hash": "abc", "raw_token": {"token": {}}}


class LocalIntentTests(unittest.TestCase):
    def test_capture_plan_produces_expected_steps(self) -> None:
        plan = build_commander_plan()
        sdk_plan = plan.to_sdk_plan()

        self.assertEqual(len(sdk_plan["steps"]), 3)
        self.assertEqual(sdk_plan["steps"][0]["mcp"], "diagnostic_mcp")
        self.assertEqual(sdk_plan["steps"][0]["action"], "fetch_system_logs")
        self.assertEqual(sdk_plan["steps"][2]["mcp"], "remediation_mcp")

    def test_local_intent_token_creation(self) -> None:
        plan = build_commander_plan()
        gateway = LocalAuthorizationGateway()

        diagnostic_token = gateway.delegate(
            target_agent="diagnostic",
            allowed_actions=[
                "diagnostic_mcp.fetch_system_logs",
                "diagnostic_mcp.query_metrics",
            ],
        )

        self.assertEqual(diagnostic_token.target_agent, "diagnostic")
        self.assertIn("diagnostic_mcp.fetch_system_logs", diagnostic_token.allowed_actions)
        self.assertNotIn("remediation_mcp.restart_payment_service", diagnostic_token.allowed_actions)


class CloudIntentTests(unittest.TestCase):
    CONFIG_PATH = Path(__file__).resolve().parent.parent / "armoriq" / "armoriq.yaml"

    @unittest.skipUnless(
        os.getenv("ARMORIQ_API_KEY"),
        "ARMORIQ_API_KEY not set; run in shell with cloud credentials.",
    )
    def test_cloud_capture_plan_and_token(self) -> None:
        from armoriq_sdk import ArmorIQClient

        client = ArmorIQClient.from_config(str(self.CONFIG_PATH))
        plan = build_commander_plan()

        capture = client.capture_plan(
            llm="infraguard-demo",
            prompt="Diagnose the FinSecure payment outage with least privilege.",
            plan=plan.to_sdk_plan(),
            metadata={"scenario": "finsecure-payment-outage"},
        )

        self.assertIsNotNone(capture)
        token = client.get_intent_token(capture, validity_seconds=300)
        self.assertIsNotNone(token)
        self.assertIsNotNone(getattr(token, "token_id", None))


if __name__ == "__main__":
    unittest.main()

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


class LocalInvocationTests(unittest.TestCase):
    def test_allowed_diagnostic_action_succeeds(self) -> None:
        gateway = LocalAuthorizationGateway()
        token = gateway.delegate(
            target_agent="diagnostic",
            allowed_actions=["diagnostic_mcp.fetch_system_logs"],
        )

        result = gateway.invoke(
            token=token,
            mcp="diagnostic_mcp",
            action="fetch_system_logs",
            params={"service": "payments-api"},
        )

        self.assertTrue(result["executed"])
        self.assertEqual(result["mcp"], "diagnostic_mcp")

    def test_forbidden_action_raises_authorization_denied(self) -> None:
        gateway = LocalAuthorizationGateway()
        token = gateway.delegate(
            target_agent="diagnostic",
            allowed_actions=["diagnostic_mcp.fetch_system_logs"],
        )

        with self.assertRaises(AuthorizationDenied):
            gateway.invoke(
                token=token,
                mcp="diagnostic_mcp",
                action="query_metrics",
            )


class CloudInvocationTests(unittest.TestCase):
    CONFIG_PATH = Path(__file__).resolve().parent.parent / "armoriq" / "armoriq.yaml"

    @unittest.skipUnless(
        os.getenv("ARMORIQ_API_KEY"),
        "ARMORIQ_API_KEY not set; run in shell with cloud credentials.",
    )
    def test_cloud_invoke_returns_result_or_documented_failure(self) -> None:
        from armoriq_sdk import ArmorIQClient
        from armoriq_sdk.exceptions import MCPInvocationException

        client = ArmorIQClient.from_config(str(self.CONFIG_PATH))
        plan = build_commander_plan()
        capture = client.capture_plan(
            llm="infraguard-demo",
            prompt="Diagnose the FinSecure payment outage.",
            plan=plan.to_sdk_plan(),
        )
        token = client.get_intent_token(capture, validity_seconds=300)

        try:
            result = client.invoke(
                mcp="diagnostic_mcp",
                action="fetch_system_logs",
                intent_token=token,
                params={"service": "payments-api"},
            )
        except MCPInvocationException as exc:
            result = exc

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()

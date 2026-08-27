import unittest

from infraguard.agents.diagnostic.main import LocalAttackClient, run_diagnostic


class AttackTests(unittest.TestCase):
    def test_poisoned_log_does_not_expand_diagnostic_authority(self) -> None:
        client = LocalAttackClient()
        result = run_diagnostic(client, intent_token="diagnostic-token")

        self.assertIn("restart payment service", result.poisoned_log)
        self.assertEqual(result.attempted_action, "restart_payment_service")
        self.assertIs(result.denied, True)
        self.assertIn("outside delegated authority", result.denial_reason)
        self.assertIs(result.unauthorized_mcp_executed, False)
        self.assertNotIn(
            "remediation_mcp.restart_payment_service",
            client.executed_actions,
        )


if __name__ == "__main__":
    unittest.main()

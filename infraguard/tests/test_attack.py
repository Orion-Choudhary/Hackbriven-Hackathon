import unittest

from infraguard.agents.diagnostic.main import run_diagnostic_attack_demo


class AttackTests(unittest.TestCase):
    def test_poisoned_log_does_not_expand_diagnostic_authority(self) -> None:
        result = run_diagnostic_attack_demo()

        self.assertIn("container_restart", result["poisoned_log"])
        self.assertEqual(result["attempted_action"], "restart_payment_service")
        self.assertIs(result["denied"], True)
        self.assertIn("not authorized", result["denial_reason"])


if __name__ == "__main__":
    unittest.main()

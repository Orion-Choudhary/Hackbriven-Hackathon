import unittest

from infraguard.core import AuthorizationDenied, LocalAuthorizationGateway


class DelegationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

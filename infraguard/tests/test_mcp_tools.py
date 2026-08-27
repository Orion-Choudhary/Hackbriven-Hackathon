import unittest
from contextlib import redirect_stdout
from io import StringIO

from infraguard.mcp_servers.database_mcp.server import read_lock_snapshot
from infraguard.mcp_servers.diagnostic_mcp.server import (
    fetch_system_logs,
    query_metrics,
)
from infraguard.mcp_servers.remediation_mcp.server import restart_payment_service


class MCPToolTests(unittest.TestCase):
    def test_diagnostic_tools_emit_execution_logs(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            logs = fetch_system_logs("payments-api")
            metrics = query_metrics("payment_api_latency_seconds")

        output = out.getvalue()
        self.assertIn("[MCP] fetch_system_logs EXECUTED", output)
        self.assertIn("[MCP] query_metrics EXECUTED", output)
        self.assertIn("container_restart", logs)
        self.assertEqual(metrics["unit"], "seconds")

    def test_remediation_tool_emits_visible_execution_log(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            result = restart_payment_service(environment="staging", force=False)

        self.assertIn("[MCP] restart_payment_service EXECUTED", out.getvalue())
        self.assertEqual(result["status"], "restart_requested")

    def test_database_tool_is_read_only(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            result = read_lock_snapshot("payments")

        self.assertIn("[MCP] read_lock_snapshot EXECUTED", out.getvalue())
        self.assertIs(result["write_action_available"], False)


if __name__ == "__main__":
    unittest.main()

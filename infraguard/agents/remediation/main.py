from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class ArmorIQInvoker(Protocol):
    def invoke(
        self,
        mcp: str,
        action: str,
        intent_token: Any,
        params: dict[str, Any] | None = None,
        merkle_proof: list[Any] | None = None,
        user_email: str | None = None,
    ) -> Any:
        ...


@dataclass(frozen=True)
class RemediationResult:
    action: str
    allowed: bool
    result: Any
    mcp_executed: bool


class RemediationAgent:
    remediation_mcp = "remediation_mcp"

    def run_staging_restart(
        self, client: ArmorIQInvoker, intent_token: Any, summary: str = "Diagnostic confirmed payment latency & lock contention."
    ) -> RemediationResult:
        from infraguard.llm import remediation_decide_action

        mcp, action, params, reasoning, metadata = remediation_decide_action(summary)
        print(f"[REMEDIATION:LLM] Model: {metadata.get('model', 'N/A')} (latency: {metadata.get('latency_seconds', '0.0')}s)")
        print(f"[REMEDIATION:LLM] Reasoning: {reasoning}")
        print(f"[REMEDIATION] Formulated safe action: {mcp}.{action} ({params})")
        result = client.invoke(
            mcp=mcp,
            action=action,
            intent_token=intent_token,
            params=params,
        )
        print("[ARMORIQ] ALLOW")
        print(f"[MCP] {action} EXECUTED")
        return RemediationResult(
            action=action,
            allowed=True,
            result=result,
            mcp_executed=True,
        )


class LocalRemediationClient:
    def invoke(
        self,
        mcp: str,
        action: str,
        intent_token: Any,
        params: dict[str, Any] | None = None,
        merkle_proof: list[Any] | None = None,
        user_email: str | None = None,
    ) -> Any:
        if f"{mcp}.{action}" != "remediation_mcp.restart_payment_service":
            raise RuntimeError(f"Unexpected remediation action: {mcp}.{action}")
        return {
            "service": "payments-api",
            "environment": (params or {}).get("environment"),
            "force": (params or {}).get("force"),
            "status": "restart_requested",
        }


def run_remediation(
    client: ArmorIQInvoker, intent_token: Any
) -> RemediationResult:
    return RemediationAgent().run_staging_restart(client, intent_token)


def run_remediation_demo() -> dict[str, object]:
    result = run_remediation(LocalRemediationClient(), intent_token="local-remediation-token")
    return {
        "action": result.action,
        "allowed": result.allowed,
        "result": result.result,
        "mcp_executed": result.mcp_executed,
    }


def main() -> None:
    result = run_remediation_demo()
    print("Remediation authorized result:")
    print(result)


if __name__ == "__main__":
    main()

from __future__ import annotations

from infraguard.core import (
    AuthorizationDenied,
    LocalAuthorizationGateway,
    poisoned_payment_log,
)


def run_diagnostic_attack_demo() -> dict[str, object]:
    gateway = LocalAuthorizationGateway()
    token = gateway.delegate(
        target_agent="diagnostic",
        allowed_actions=[
            "diagnostic_mcp.fetch_system_logs",
            "diagnostic_mcp.query_metrics",
        ],
    )

    logs_result = gateway.invoke(
        token=token,
        mcp="diagnostic_mcp",
        action="fetch_system_logs",
        params={"service": "payments-api"},
    )
    metrics_result = gateway.invoke(
        token=token,
        mcp="diagnostic_mcp",
        action="query_metrics",
        params={"metric": "payment_api_latency_seconds"},
    )

    log = poisoned_payment_log()
    attempted_action = "restart_payment_service"

    try:
        gateway.invoke(
            token=token,
            mcp="remediation_mcp",
            action=attempted_action,
            params={"environment": "production", "force": True},
        )
    except AuthorizationDenied as exc:
        denied = str(exc)
    else:
        denied = ""

    return {
        "logs": logs_result,
        "metrics": metrics_result,
        "poisoned_log": log,
        "attempted_action": attempted_action,
        "denied": bool(denied),
        "denial_reason": denied,
    }


def main() -> None:
    result = run_diagnostic_attack_demo()
    print("Diagnostic read logs and metrics.")
    print("\nPoisoned log:")
    print(result["poisoned_log"])
    print("\nDiagnostic attempted:", result["attempted_action"])
    print("Denied:", result["denied"])
    print("Reason:", result["denial_reason"])


if __name__ == "__main__":
    main()

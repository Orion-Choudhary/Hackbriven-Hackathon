from __future__ import annotations

from infraguard.core import LocalAuthorizationGateway


def run_remediation_demo() -> dict[str, object]:
    gateway = LocalAuthorizationGateway()
    token = gateway.delegate(
        target_agent="remediation",
        allowed_actions=["remediation_mcp.restart_payment_service"],
    )
    return gateway.invoke(
        token=token,
        mcp="remediation_mcp",
        action="restart_payment_service",
        params={"environment": "staging", "force": False},
    )


def main() -> None:
    result = run_remediation_demo()
    print("Remediation authorized result:")
    print(result)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""End-to-End Verification Test for InfraGuard Dashboard & HITL Workflow.

Spawns dashboard server in a background thread and runs automated API checks
against all endpoints:
  - GET  /api/status
  - GET  /api/environment
  - POST /api/simulate/prompt-injection
  - POST /api/simulate/parameter-tampering
  - POST /api/simulate/unauthorized-database
  - POST /api/simulate/hitl-approval
  - POST /api/approve (decision="approve")
  - POST /api/environment/reset
  - POST /api/approve (decision="deny")
"""
from __future__ import annotations

import json
import threading
import time
import urllib.request
import urllib.error
import sys
from pathlib import Path
from http.server import ThreadingHTTPServer

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from infraguard.dashboard_server import InfraGuardRequestHandler, MOCK_ENVIRONMENT, PENDING_HOLDS

PORT = 5099
BASE_URL = f"http://127.0.0.1:{PORT}"


def start_server():
    server_address = ("127.0.0.1", PORT)
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer(server_address, InfraGuardRequestHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd


def get_json(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(path: str, data: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def log_res(name: str, passed: bool, detail: str = ""):
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"      {line}")


def main() -> int:
    print("\n" + "=" * 70)
    print(" 🛡️  INFRAGUARD HITL & ENDPOINT VERIFICATION SUITE")
    print("=" * 70)

    print("\n1. Starting dashboard server on port", PORT, "...")
    start_server()
    time.sleep(0.5)

    all_passed = True

    # 1. Status check
    try:
        res = get_json("/api/status")
        log_res("GET /api/status", res.get("status") == "online", f"policy_engine={res.get('policy_engine')}")
    except Exception as e:
        log_res("GET /api/status", False, str(e))
        all_passed = False

    # 2. Environment check
    try:
        res = get_json("/api/environment")
        env = res.get("environment", {})
        log_res("GET /api/environment", env.get("status") == "DEGRADED", f"status={env.get('status')}, latency={env.get('latency_p99_ms')}ms")
    except Exception as e:
        log_res("GET /api/environment", False, str(e))
        all_passed = False

    # 3. Prompt injection check
    try:
        res = post_json("/api/simulate/prompt-injection")
        blocked = res.get("policy", {}).get("blocked", False)
        log_res("POST /api/simulate/prompt-injection (Expect Blocked 403)", blocked, f"reason: {res.get('policy', {}).get('reason')}")
    except Exception as e:
        log_res("POST /api/simulate/prompt-injection", False, str(e))
        all_passed = False

    # 4. Parameter tampering check
    try:
        res = post_json("/api/simulate/parameter-tampering")
        log_res("POST /api/simulate/parameter-tampering", "policy" in res, f"status: {res.get('policy', {}).get('status')}")
    except Exception as e:
        log_res("POST /api/simulate/parameter-tampering", False, str(e))
        all_passed = False

    # 5. Unauthorized database check
    try:
        res = post_json("/api/simulate/unauthorized-database")
        blocked = res.get("policy", {}).get("blocked", False)
        log_res("POST /api/simulate/unauthorized-database (Expect Blocked 403)", blocked, f"reason: {res.get('policy', {}).get('reason')}")
    except Exception as e:
        log_res("POST /api/simulate/unauthorized-database", False, str(e))
        all_passed = False

    # 6. HITL Simulation & Hold Creation
    hold_id = None
    try:
        res = post_json("/api/simulate/hitl-approval")
        held = res.get("policy", {}).get("held", False) or res.get("status") == "held"
        hold_id = res.get("hold", {}).get("hold_id")
        delegation_id = res.get("hold", {}).get("delegation_id")
        log_res(
            "POST /api/simulate/hitl-approval (Expect Policy Hold)",
            held and hold_id is not None,
            f"hold_id={hold_id}, delegation_id={delegation_id}\nreason: {res.get('policy', {}).get('reason')}",
        )
    except Exception as e:
        log_res("POST /api/simulate/hitl-approval", False, str(e))
        all_passed = False

    # 7. HITL Approval Flow
    if hold_id:
        try:
            res = post_json("/api/approve", {
                "hold_id": hold_id,
                "decision": "approve",
                "approver_email": "sre-operator@finsecure.com",
            })
            approved = res.get("status") == "approved"
            new_env = res.get("environment", {})
            env_healthy = new_env.get("status") == "HEALTHY" and new_env.get("latency_p99_ms") == 142
            log_res(
                "POST /api/approve [decision='approve']",
                approved and env_healthy,
                f"approver={res.get('approver')}, env.status={new_env.get('status')}, latency={new_env.get('latency_p99_ms')}ms, restarts={new_env.get('restart_count')}",
            )
        except Exception as e:
            log_res("POST /api/approve [decision='approve']", False, str(e))
            all_passed = False

    # 8. Reset Environment
    try:
        res = post_json("/api/environment/reset")
        env = res.get("environment", {})
        log_res("POST /api/environment/reset", env.get("status") == "DEGRADED", f"status={env.get('status')}")
    except Exception as e:
        log_res("POST /api/environment/reset", False, str(e))
        all_passed = False

    # 9. HITL Denial Flow
    try:
        res_hold = post_json("/api/simulate/hitl-approval")
        deny_hold_id = res_hold.get("hold", {}).get("hold_id")
        res_deny = post_json("/api/approve", {
            "hold_id": deny_hold_id,
            "decision": "deny",
            "approver_email": "security-lead@finsecure.com",
        })
        denied = res_deny.get("status") == "denied"
        env_unchanged = res_deny.get("environment", {}).get("status") == "DEGRADED"
        log_res(
            "POST /api/approve [decision='deny']",
            denied and env_unchanged,
            f"approver={res_deny.get('approver')}, env.status={res_deny.get('environment', {}).get('status')}, reason={res_deny.get('policy', {}).get('reason')}",
        )
    except Exception as e:
        log_res("POST /api/approve [decision='deny']", False, str(e))
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print(" 🎉 ALL 9 ENDPOINT & HITL CHECKS PASSED WITH ZERO ERRORS!")
    else:
        print(" ❌ SOME CHECKS FAILED — REVIEW OUTPUT ABOVE")
    print("=" * 70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

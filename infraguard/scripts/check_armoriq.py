#!/usr/bin/env python3
"""Diagnostic script for verifying ArmorIQ SDK environment.

Prints SDK installation info, resolved endpoints, registered MCPs, and tools.
Never prints the raw API key or full tokens.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "armoriq" / "armoriq.yaml"


def mask(value: str | None, visible: int = 4) -> str:
    if not value:
        return "<not set>"
    if len(value) <= visible * 2:
        return "*" * len(value)
    return f"{value[:visible]}...{value[-visible:]}"


def _load_env_file() -> None:
    for env_path in [
        Path(".env"),
        Path("../.env"),
        Path(__file__).resolve().parents[1] / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]:
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
            break


def main() -> int:
    _load_env_file()
    print("[InfraGuard] ArmorIQ environment check")
    print("=" * 50)

    try:
        import armoriq_sdk

        print(f"SDK installed: yes")
        print(f"SDK path: {armoriq_sdk.__file__}")
    except ImportError:
        print("SDK installed: no")
        return 1

    api_key = os.getenv("ARMORIQ_API_KEY")
    print(f"ARMORIQ_API_KEY: {mask(api_key)}")

    try:
        from armoriq_sdk import ArmorIQClient

        client = ArmorIQClient.from_config(str(CONFIG_PATH))
        print(f"backend: {getattr(client, 'backend_endpoint', None)}")
        print(f"iap: {getattr(client, 'iap_endpoint', None)}")
        print(f"proxy: {getattr(client, 'default_proxy_endpoint', None)}")
        print(f"user_id: {getattr(client, 'user_id', None)}")
        print(f"agent_id: {getattr(client, 'agent_id', None)}")

        print("\nRegistered MCPs:")
        try:
            mcps = client.list_mcps()
            if not mcps:
                print("  <none>")
            for mcp in mcps:
                print(f"  - {mcp.get('name')}: {mcp.get('url')}")
        except Exception as exc:
            print(f"  list_mcps() failed: {exc}")

        print("\nTool schemas:")
        try:
            mcps = client.list_mcps()
            for mcp in mcps:
                name = mcp.get("name")
                tools = client.get_mcp_tool_schemas(name)
                print(f"  {name}:")
                for tool in tools:
                    print(f"    - {tool.get('name')}")
        except Exception as exc:
            print(f"  get_mcp_tool_schemas() failed: {exc}")

    except Exception as exc:
        print(f"Client initialization failed: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

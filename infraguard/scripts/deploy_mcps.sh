#!/usr/bin/env bash
set -euo pipefail

echo "Deploy Diagnostic, Remediation, and Database MCP services separately."
echo "Each service must expose only its intended tools over Streamable HTTP."
echo "Register stable HTTPS MCP endpoints with ArmorIQ after deployment."

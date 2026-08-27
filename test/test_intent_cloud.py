from armoriq_sdk import ArmorIQClient


client = ArmorIQClient(
    api_key="ak_live_988c5037688dfe0020c90ce45bed336b304173112b6f46c58071abd0083f79bc",
    user_id="Test-services",
    agent_id="Test",
    backend_endpoint="https://api.armoriq.ai",
    iap_endpoint="https://iap.armoriq.ai",
    proxy_endpoint="https://proxy.armoriq.ai",
    use_production=True,
)


print("backend:", client.backend_endpoint)
print("iap:", client.iap_endpoint)
print("proxy:", client.proxy_endpoint)


plan = {
    "steps": [
        {
            "mcp": "trycloudflare",
            "action": "echo",
            "params": {
                "message": "Hello from ArmorIQ"
            },
        }
    ]
}


print("1. Capturing plan...")

plan_capture = client.capture_plan(
    llm="gpt-4o",
    prompt="Test authorized echo invocation",
    plan=plan,
)

print("   ✓ Plan captured")

print("2. Creating intent token...")

intent_token = client.get_intent_token(
    plan_capture,
    validity_seconds=300,
)

print("   ✓ Intent token created")

print("3. Invoking echo through ArmorIQ...")

try:
    result = client.invoke(
        mcp="trycloudflare",
        action="echo",
        intent_token=intent_token,
        params={"message": "hello from InfraGuard"},
    )

    print("   ✓ Invocation succeeded")
    print("   Result:", result)

except Exception as e:
    print("   ✗ Invocation failed")
    print("   Exception:", type(e).__name__)
    print("   Message:", str(e))

    if hasattr(e, "status_code"):
        print("   Status:", e.status_code)
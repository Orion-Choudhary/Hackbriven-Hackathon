from armoriq_sdk import ArmorIQClient


client = ArmorIQClient.from_config("armoriq-test.yaml")


# 1. Define the authorized plan
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


# 2. Create intent token
print("2. Creating intent token...")

intent_token = client.get_intent_token(
    plan_capture,
    validity_seconds=300,
)

print("   ✓ Intent token created")


# 3. Invoke the authorized action
print("3. Invoking echo through ArmorIQ...")

result = client.invoke(
    mcp="trycloudflare",
    action="echo",
    intent_token=intent_token,
    params={
        "message": "Hello from ArmorIQ"
    },
)

print("   ✓ Invocation completed")
print("   Result:", result)
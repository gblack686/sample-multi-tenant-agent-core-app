"""
Hello World test for the multi-tenant Bedrock Agent Core sample app.

Tests four levels of Bedrock AI invocation:
1. Direct Claude invocation via bedrock-runtime (simplest path)
2. Multi-tenant context injection (the sample app's core pattern)
3. Inline Agent with session state (no pre-created agent needed)
4. AgentCore Runtime invocation (full AgentCore infrastructure)
"""

import boto3
import json
import uuid
import sys
from datetime import datetime, timezone


REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def test_1_direct_claude_invocation():
    """Test 1: Direct Claude model call via Bedrock - simplest path"""
    print("\n" + "=" * 60)
    print("TEST 1: Direct Claude Invocation via Bedrock")
    print("=" * 60)

    client = boto3.client("bedrock-runtime", region_name=REGION)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 256,
        "messages": [{"role": "user", "content": "Say hello world in one sentence."}],
    }

    print(f"  Model: {MODEL_ID}")
    print(f"  API: bedrock-runtime invoke_model")

    response = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    response_body = json.loads(response["body"].read())
    text = response_body["content"][0]["text"]
    usage = response_body.get("usage", {})

    print(f"  Response: {text}")
    print(f"  Tokens: {usage.get('input_tokens', 0)} in / {usage.get('output_tokens', 0)} out")
    print("  PASS")
    return True


def test_2_multi_tenant_context():
    """Test 2: Direct Claude with multi-tenant session context (the sample app's pattern)"""
    print("\n" + "=" * 60)
    print("TEST 2: Multi-Tenant Context Pattern")
    print("=" * 60)

    client = boto3.client("bedrock-runtime", region_name=REGION)

    tenant_id = "acme-corp"
    user_id = "user-001"
    subscription_tier = "premium"
    session_id = str(uuid.uuid4())[:8]
    composite_session_id = f"{tenant_id}-{subscription_tier}-{user_id}-{session_id}"

    system_prompt = (
        f"You are an AI assistant for tenant '{tenant_id}' "
        f"(subscription: {subscription_tier}). "
        f"Current user: {user_id}. Session: {composite_session_id}. "
        f"Respond briefly."
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 256,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": "What tenant am I from and what is my subscription tier?",
            }
        ],
    }

    print(f"  Tenant: {tenant_id} | User: {user_id} | Tier: {subscription_tier}")
    print(f"  Session: {composite_session_id}")
    print(f"  API: bedrock-runtime invoke_model (with system prompt)")

    response = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    response_body = json.loads(response["body"].read())
    text = response_body["content"][0]["text"]
    usage = response_body.get("usage", {})

    cost_record = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "session_id": composite_session_id,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "invocation_time": datetime.now(timezone.utc).isoformat(),
    }

    print(f"  Response: {text}")
    print(f"  Cost record: {json.dumps(cost_record, indent=4)}")
    print("  PASS")
    return True


def test_3_inline_agent():
    """Test 3: Inline Agent with session state - no pre-created agent needed"""
    print("\n" + "=" * 60)
    print("TEST 3: Inline Agent with Multi-Tenant Session State")
    print("=" * 60)

    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    session_id = f"inline-{uuid.uuid4().hex[:8]}"

    print(f"  Session: {session_id}")
    print(f"  API: bedrock-agent-runtime invoke_inline_agent")
    print(f"  Model: {MODEL_ID}")

    response = client.invoke_inline_agent(
        foundationModel=MODEL_ID,
        instruction="You are a helpful AI assistant for a multi-tenant SaaS platform. Respond briefly.",
        sessionId=session_id,
        inputText="Hello world! What tenant am I and what is my subscription tier?",
        enableTrace=True,
        inlineSessionState={
            "sessionAttributes": {
                "tenant_id": "acme-corp",
                "user_id": "user-001",
                "subscription_tier": "premium",
            },
            "promptSessionAttributes": {
                "tenant_context": "acme-corp premium user",
            },
        },
    )

    text = ""
    trace_count = 0
    for event in response["completion"]:
        if "chunk" in event and "bytes" in event["chunk"]:
            text += event["chunk"]["bytes"].decode("utf-8")
        elif "trace" in event:
            trace_count += 1

    print(f"  Response: {text}")
    print(f"  Orchestration traces: {trace_count}")
    print("  PASS")
    return True


def test_4_agentcore_runtime():
    """Test 4: Full AgentCore Runtime invocation"""
    print("\n" + "=" * 60)
    print("TEST 4: AgentCore Runtime (bedrock-agentcore)")
    print("=" * 60)

    # List available AgentCore runtimes
    control_client = boto3.client("bedrock-agentcore-control", region_name=REGION)

    try:
        response = control_client.list_agent_runtimes()
        runtimes = response.get("agentRuntimes", [])
    except Exception as e:
        print(f"  Could not list runtimes: {e}")
        print("  SKIP - AgentCore not available")
        return None

    ready_runtimes = [r for r in runtimes if r["status"] == "READY"]
    if not ready_runtimes:
        print(f"  Found {len(runtimes)} runtime(s) but none in READY state")
        print("  SKIP - No ready runtimes")
        return None

    runtime = ready_runtimes[0]
    runtime_arn = runtime["agentRuntimeArn"]
    print(f"  Runtime: {runtime['agentRuntimeName']} (v{runtime['agentRuntimeVersion']})")
    print(f"  ARN: {runtime_arn}")
    print(f"  API: bedrock-agentcore invoke_agent_runtime")

    # Invoke via AgentCore
    ac_client = boto3.client("bedrock-agentcore", region_name=REGION)
    session_id = str(uuid.uuid4())

    response = ac_client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=session_id,
        payload=json.dumps({"query": "Hello world! Say hi briefly."}).encode("utf-8"),
    )

    print(f"  Status: {response['statusCode']}")
    print(f"  Session: {response.get('runtimeSessionId')}")
    print(f"  Trace: {response.get('traceId', 'N/A')}")

    # Read streaming response
    stream = response.get("response")
    if stream:
        raw = stream.read().decode("utf-8", errors="replace")
        # Parse SSE data lines
        for line in raw.strip().split("\n"):
            if line.startswith("data: "):
                data = line[6:]
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, str):
                        # Truncate long responses
                        display = parsed[:500] + "..." if len(parsed) > 500 else parsed
                        print(f"  Response: {display}")
                    else:
                        print(f"  Response: {json.dumps(parsed, indent=2)[:500]}")
                except json.JSONDecodeError:
                    print(f"  Response (raw): {data[:500]}")

    print("  PASS")
    return True


def main():
    print("=" * 60)
    print("Multi-Tenant Bedrock Agent Core - Hello World Validation")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"Region: {REGION}")
    print("=" * 60)

    tests = [
        ("1_direct_claude", test_1_direct_claude_invocation),
        ("2_multi_tenant", test_2_multi_tenant_context),
        ("3_inline_agent", test_3_inline_agent),
        ("4_agentcore_runtime", test_4_agentcore_runtime),
    ]

    results = {}
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"  FAIL: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, result in results.items():
        status = "PASS" if result is True else ("SKIP" if result is None else "FAIL")
        print(f"  {name}: {status}")

    passed = sum(1 for r in results.values() if r is True)
    skipped = sum(1 for r in results.values() if r is None)
    failed = sum(1 for r in results.values() if r is False)
    print(f"\n  {passed} passed, {skipped} skipped, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

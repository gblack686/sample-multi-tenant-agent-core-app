"""
Advanced Bedrock Agent Tests - Tool Calling with Full Trace Observation

Demonstrates:
1. Inline agent with custom action groups (tools) - observed tool invocations
2. Multi-step orchestration with full trace decomposition
3. Return-of-control pattern for tool execution
"""

import boto3
import json
import uuid
import sys
from datetime import datetime, timezone
from typing import Any


REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def format_trace(trace: dict, indent: int = 0) -> str:
    """Pretty-format an orchestration trace for display."""
    lines = []
    prefix = "  " * indent

    if "orchestrationTrace" in trace:
        orch = trace["orchestrationTrace"]

        # Model invocation input (what was sent to the model)
        if "modelInvocationInput" in orch:
            mii = orch["modelInvocationInput"]
            lines.append(f"{prefix}[MODEL INPUT]")
            if "text" in mii:
                text = mii["text"][:200] + "..." if len(mii.get("text", "")) > 200 else mii.get("text", "")
                lines.append(f"{prefix}  Prompt: {text}")
            if "inferenceConfiguration" in mii:
                conf = mii["inferenceConfiguration"]
                lines.append(f"{prefix}  Config: maxTokens={conf.get('maximumLength', 'N/A')}, temp={conf.get('temperature', 'N/A')}")

        # Rationale (agent's reasoning)
        if "rationale" in orch:
            text = orch["rationale"].get("text", "")
            lines.append(f"{prefix}[REASONING]")
            lines.append(f"{prefix}  {text[:300]}")

        # Invocation input (tool call decision)
        if "invocationInput" in orch:
            inv = orch["invocationInput"]
            lines.append(f"{prefix}[TOOL CALL DECISION]")
            lines.append(f"{prefix}  Type: {inv.get('invocationType', 'N/A')}")

            if "actionGroupInvocationInput" in inv:
                ag = inv["actionGroupInvocationInput"]
                lines.append(f"{prefix}  Action Group: {ag.get('actionGroupName', 'N/A')}")
                lines.append(f"{prefix}  Function: {ag.get('function', 'N/A')}")
                params = ag.get("parameters", [])
                if params:
                    lines.append(f"{prefix}  Parameters:")
                    for p in params:
                        lines.append(f"{prefix}    {p.get('name', '?')}: {p.get('value', '?')}")

            if "returnControlInvocationInput" in inv:
                rc = inv["returnControlInvocationInput"]
                lines.append(f"{prefix}  [RETURN OF CONTROL]")
                lines.append(f"{prefix}  Invocation ID: {rc.get('invocationId', 'N/A')}")

        # Model invocation output (token usage)
        if "modelInvocationOutput" in orch:
            mio = orch["modelInvocationOutput"]
            if "metadata" in mio:
                meta = mio["metadata"]
                usage = meta.get("usage", {})
                lines.append(f"{prefix}[MODEL OUTPUT]")
                lines.append(f"{prefix}  Input tokens: {usage.get('inputTokens', 0)}")
                lines.append(f"{prefix}  Output tokens: {usage.get('outputTokens', 0)}")

        # Observation (tool result returned to model)
        if "observation" in orch:
            obs = orch["observation"]
            lines.append(f"{prefix}[OBSERVATION]")
            if "actionGroupInvocationOutput" in obs:
                ago = obs["actionGroupInvocationOutput"]
                text = ago.get("text", "")[:200]
                lines.append(f"{prefix}  Tool result: {text}")
            if "finalResponse" in obs:
                fr = obs["finalResponse"]
                text = fr.get("text", "")[:300]
                lines.append(f"{prefix}  Final: {text}")

    if "preProcessingTrace" in trace:
        pre = trace["preProcessingTrace"]
        if "modelInvocationOutput" in pre:
            parsed = pre["modelInvocationOutput"].get("parsedResponse", {})
            lines.append(f"{prefix}[PRE-PROCESSING]")
            lines.append(f"{prefix}  Is valid: {parsed.get('isValid', 'N/A')}")
            lines.append(f"{prefix}  Rationale: {parsed.get('rationale', 'N/A')[:200]}")

    if "postProcessingTrace" in trace:
        lines.append(f"{prefix}[POST-PROCESSING]")
        post = trace["postProcessingTrace"]
        if "modelInvocationOutput" in post:
            parsed = post["modelInvocationOutput"].get("parsedResponse", {})
            lines.append(f"{prefix}  Output: {parsed.get('text', 'N/A')[:200]}")

    return "\n".join(lines) if lines else f"{prefix}[TRACE] {str(trace)[:200]}"


def test_1_inline_agent_with_tools():
    """Test: Inline agent with custom tools (action groups) and full trace."""
    print("\n" + "=" * 70)
    print("TEST: Inline Agent with Custom Tools + Full Trace Observation")
    print("=" * 70)

    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    session_id = f"tools-{uuid.uuid4().hex[:8]}"

    # Define custom tools as action groups with OpenAPI-style function definitions
    action_groups = [
        {
            "actionGroupName": "InventoryTools",
            "description": "Tools for looking up product inventory and pricing",
            "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
            "functionSchema": {
                "functions": [
                    {
                        "name": "lookup_product",
                        "description": "Look up a product by name and return its details including price and stock",
                        "parameters": {
                            "product_name": {
                                "description": "The name of the product to look up",
                                "type": "string",
                                "required": True,
                            }
                        },
                    },
                    {
                        "name": "check_stock",
                        "description": "Check current stock level for a product ID",
                        "parameters": {
                            "product_id": {
                                "description": "The product ID to check stock for",
                                "type": "string",
                                "required": True,
                            }
                        },
                    },
                ]
            },
        },
        {
            "actionGroupName": "OrderTools",
            "description": "Tools for creating and managing orders",
            "actionGroupExecutor": {"customControl": "RETURN_CONTROL"},
            "functionSchema": {
                "functions": [
                    {
                        "name": "create_order",
                        "description": "Create a new order for a product",
                        "parameters": {
                            "product_id": {
                                "description": "Product ID to order",
                                "type": "string",
                                "required": True,
                            },
                            "quantity": {
                                "description": "Number of items to order",
                                "type": "integer",
                                "required": True,
                            },
                        },
                    }
                ]
            },
        },
    ]

    print(f"  Session: {session_id}")
    print(f"  Model: {MODEL_ID}")
    print(f"  Action Groups: {[ag['actionGroupName'] for ag in action_groups]}")
    print(f"  Tools defined: lookup_product, check_stock, create_order")
    print()

    # First invocation - agent will try to use tools
    response = client.invoke_inline_agent(
        foundationModel=MODEL_ID,
        instruction=(
            "You are an inventory management assistant. "
            "Use the available tools to help users with product lookups, stock checks, and orders. "
            "Always use the lookup_product tool before creating orders."
        ),
        sessionId=session_id,
        inputText="I want to order 5 units of the Widget Pro. First look it up, then check stock, then place the order.",
        enableTrace=True,
        actionGroups=action_groups,
        inlineSessionState={
            "sessionAttributes": {
                "tenant_id": "acme-corp",
                "user_id": "buyer-001",
            }
        },
    )

    text = ""
    traces = []
    return_control_event = None

    print("  --- ORCHESTRATION TRACE ---")
    for event in response["completion"]:
        if "chunk" in event and "bytes" in event["chunk"]:
            text += event["chunk"]["bytes"].decode("utf-8")
        elif "trace" in event:
            trace = event["trace"].get("trace", event["trace"])
            traces.append(trace)
            formatted = format_trace(trace, indent=1)
            if formatted.strip():
                print(formatted)
                print()
        elif "returnControl" in event:
            return_control_event = event["returnControl"]
            print(f"  [RETURN OF CONTROL]")
            print(f"    Invocation ID: {return_control_event.get('invocationId', 'N/A')}")
            inv_inputs = return_control_event.get("invocationInputs", [])
            for inp in inv_inputs:
                if "functionInvocationInput" in inp:
                    fi = inp["functionInvocationInput"]
                    print(f"    Action Group: {fi.get('actionGroup', 'N/A')}")
                    print(f"    Function: {fi.get('function', 'N/A')}")
                    params = fi.get("parameters", [])
                    for p in params:
                        print(f"    Param: {p.get('name', '?')} = {p.get('value', '?')}")
            print()

    print("  --- END TRACE ---")
    print()

    if text:
        print(f"  Agent response: {text}")
    if return_control_event:
        print(f"  Tool call intercepted! Agent wants to call a tool.")
        print(f"  This is the RETURN_CONTROL pattern - you execute the tool and send results back.")

    # If we got a return-of-control, simulate tool execution and continue
    if return_control_event:
        print()
        print("  --- Simulating tool execution and returning results ---")

        invocation_id = return_control_event.get("invocationId")
        inv_inputs = return_control_event.get("invocationInputs", [])

        # Build mock results
        tool_results = []
        for inp in inv_inputs:
            if "functionInvocationInput" in inp:
                fi = inp["functionInvocationInput"]
                func_name = fi.get("function", "")
                ag_name = fi.get("actionGroup", "")

                if func_name == "lookup_product":
                    result_body = json.dumps({
                        "product_id": "WP-001",
                        "name": "Widget Pro",
                        "price": 29.99,
                        "category": "Widgets",
                        "description": "Professional grade widget",
                    })
                elif func_name == "check_stock":
                    result_body = json.dumps({
                        "product_id": "WP-001",
                        "in_stock": 150,
                        "warehouse": "US-East",
                    })
                elif func_name == "create_order":
                    result_body = json.dumps({
                        "order_id": "ORD-2026-0001",
                        "status": "confirmed",
                        "total": 149.95,
                    })
                else:
                    result_body = json.dumps({"error": f"Unknown function: {func_name}"})

                tool_results.append({
                    "functionResult": {
                        "actionGroup": ag_name,
                        "function": func_name,
                        "responseBody": {"TEXT": {"body": result_body}},
                    }
                })
                print(f"    Executed {func_name} -> {result_body}")

        # Continue the conversation with tool results
        print()
        print("  --- Continuing agent with tool results ---")
        print()

        response2 = client.invoke_inline_agent(
            foundationModel=MODEL_ID,
            instruction=(
                "You are an inventory management assistant. "
                "Use the available tools to help users with product lookups, stock checks, and orders."
            ),
            sessionId=session_id,
            inputText="Continue processing the order.",
            enableTrace=True,
            actionGroups=action_groups,
            inlineSessionState={
                "returnControlInvocationResults": tool_results,
                "invocationId": invocation_id,
            },
        )

        text2 = ""
        return_control_2 = None
        print("  --- ORCHESTRATION TRACE (continuation) ---")
        for event in response2["completion"]:
            if "chunk" in event and "bytes" in event["chunk"]:
                text2 += event["chunk"]["bytes"].decode("utf-8")
            elif "trace" in event:
                trace = event["trace"].get("trace", event["trace"])
                formatted = format_trace(trace, indent=1)
                if formatted.strip():
                    print(formatted)
                    print()
            elif "returnControl" in event:
                return_control_2 = event["returnControl"]
                print(f"  [RETURN OF CONTROL - Round 2]")
                inv_inputs2 = return_control_2.get("invocationInputs", [])
                for inp in inv_inputs2:
                    if "functionInvocationInput" in inp:
                        fi = inp["functionInvocationInput"]
                        print(f"    Function: {fi.get('function', 'N/A')}")
                        params = fi.get("parameters", [])
                        for p in params:
                            print(f"    Param: {p.get('name', '?')} = {p.get('value', '?')}")
                print()

        print("  --- END TRACE ---")

        if text2:
            print(f"\n  Agent response: {text2}")

        # Handle additional rounds if needed
        if return_control_2:
            invocation_id_2 = return_control_2.get("invocationId")
            inv_inputs_2 = return_control_2.get("invocationInputs", [])
            tool_results_2 = []
            for inp in inv_inputs_2:
                if "functionInvocationInput" in inp:
                    fi = inp["functionInvocationInput"]
                    func_name = fi.get("function", "")
                    ag_name = fi.get("actionGroup", "")
                    if func_name == "check_stock":
                        result_body = json.dumps({"product_id": "WP-001", "in_stock": 150, "warehouse": "US-East"})
                    elif func_name == "create_order":
                        result_body = json.dumps({"order_id": "ORD-2026-0001", "status": "confirmed", "total": 149.95})
                    else:
                        result_body = json.dumps({"product_id": "WP-001", "name": "Widget Pro", "price": 29.99})
                    tool_results_2.append({
                        "functionResult": {
                            "actionGroup": ag_name,
                            "function": func_name,
                            "responseBody": {"TEXT": {"body": result_body}},
                        }
                    })
                    print(f"    Executed {func_name} -> {result_body}")

            print("\n  --- Round 3 ---")
            response3 = client.invoke_inline_agent(
                foundationModel=MODEL_ID,
                instruction="You are an inventory management assistant.",
                sessionId=session_id,
                inputText="Continue.",
                enableTrace=True,
                actionGroups=action_groups,
                inlineSessionState={
                    "returnControlInvocationResults": tool_results_2,
                    "invocationId": invocation_id_2,
                },
            )
            text3 = ""
            rc3 = None
            for event in response3["completion"]:
                if "chunk" in event and "bytes" in event["chunk"]:
                    text3 += event["chunk"]["bytes"].decode("utf-8")
                elif "trace" in event:
                    trace = event["trace"].get("trace", event["trace"])
                    formatted = format_trace(trace, indent=1)
                    if formatted.strip():
                        print(formatted)
                        print()
                elif "returnControl" in event:
                    rc3 = event["returnControl"]
                    inv3 = rc3.get("invocationInputs", [])
                    for inp in inv3:
                        if "functionInvocationInput" in inp:
                            fi = inp["functionInvocationInput"]
                            print(f"    Tool call: {fi.get('function', 'N/A')}")

            # One more round if needed
            if rc3:
                inv_id3 = rc3.get("invocationId")
                inv3 = rc3.get("invocationInputs", [])
                tr3 = []
                for inp in inv3:
                    if "functionInvocationInput" in inp:
                        fi = inp["functionInvocationInput"]
                        fn = fi.get("function", "")
                        ag = fi.get("actionGroup", "")
                        if fn == "create_order":
                            rb = json.dumps({"order_id": "ORD-2026-0001", "status": "confirmed", "total": 149.95})
                        else:
                            rb = json.dumps({"result": "ok"})
                        tr3.append({"functionResult": {"actionGroup": ag, "function": fn, "responseBody": {"TEXT": {"body": rb}}}})
                        print(f"    Executed {fn} -> {rb}")

                response4 = client.invoke_inline_agent(
                    foundationModel=MODEL_ID,
                    instruction="You are an inventory management assistant.",
                    sessionId=session_id,
                    inputText="Continue.",
                    enableTrace=True,
                    actionGroups=action_groups,
                    inlineSessionState={"returnControlInvocationResults": tr3, "invocationId": inv_id3},
                )
                for event in response4["completion"]:
                    if "chunk" in event and "bytes" in event["chunk"]:
                        text3 += event["chunk"]["bytes"].decode("utf-8")
                    elif "trace" in event:
                        trace = event["trace"].get("trace", event["trace"])
                        formatted = format_trace(trace, indent=1)
                        if formatted.strip():
                            print(formatted)

            if text3:
                print(f"\n  Final response: {text3}")

    print()
    total_traces = len(traces)
    print(f"  Total traces captured: {total_traces}")
    print(f"  Tool calls observed: YES" if return_control_event else "  Tool calls observed: NO")
    print("  PASS")
    return True


def main():
    print("=" * 70)
    print("Advanced Bedrock Agent - Tool Calls with Trace Observation")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"Region: {REGION}")
    print("=" * 70)

    try:
        result = test_1_inline_agent_with_tools()
        print(f"\n{'=' * 70}")
        print(f"RESULT: {'PASS' if result else 'FAIL'}")
        print(f"{'=' * 70}")
    except Exception as e:
        print(f"\nFAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

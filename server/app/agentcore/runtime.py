"""
AgentCore Runtime — wraps the EAGLE Strands agent as a deployable
AgentCore Runtime application.

This module provides the entry point for deploying the EAGLE agent
to AgentCore Runtime (managed serverless hosting with microVM
session isolation).

Deployment:
    agentcore launch --name eagle-agent --source ./server --entrypoint app/agentcore_runtime.py

When running on AgentCore Runtime:
    - Each user session gets an isolated microVM (no cross-contamination)
    - Auto-scales based on demand (no ECS capacity planning)
    - Supports bidirectional streaming for real-time responses
    - Identity is handled by AgentCore Identity (no manual JWT validation)

When running locally or on ECS (existing mode):
    - This module provides helper functions for Runtime-compatible responses
    - Falls back to existing FastAPI + SSE streaming
"""

import json
import logging
import os
from typing import Any, AsyncGenerator

logger = logging.getLogger("eagle.agentcore_runtime")

_RUNTIME_MODE = os.getenv("AGENTCORE_RUNTIME_MODE", "false").lower() == "true"


def is_runtime_mode() -> bool:
    """Check if running on AgentCore Runtime."""
    return _RUNTIME_MODE


def create_runtime_app():
    """Create the AgentCore Runtime application.

    Only called when deploying to Runtime. Returns a BedrockAgentCoreApp
    instance with the agent entrypoint configured.
    """
    try:
        from bedrock_agentcore.runtime import BedrockAgentCoreApp
    except ImportError:
        logger.error("bedrock-agentcore SDK not installed — cannot create Runtime app")
        return None

    app = BedrockAgentCoreApp()

    @app.entrypoint
    async def handle_request(request):
        """Main agent entry point for AgentCore Runtime.

        Receives requests from Runtime data plane and streams
        responses back via bidirectional streaming.
        """
        from app.strands_agentic_service import sdk_query_streaming

        # Extract request parameters
        body = request if isinstance(request, dict) else {}
        prompt = body.get("prompt", body.get("message", ""))
        session_id = body.get("session_id", body.get("sessionId"))
        skill_names = body.get("skill_names")

        # Identity is resolved by AgentCore Runtime + Identity
        identity = body.get("identity", {})
        tenant_id = identity.get("tenant_id", body.get("tenant_id", "demo-tenant"))
        user_id = identity.get("user_id", body.get("user_id", "demo-user"))
        tier = identity.get("tier", body.get("tier", "advanced"))

        if not prompt:
            yield {"error": "No prompt provided", "status": "error"}
            return

        # Stream response chunks
        chunks = []
        async for chunk in sdk_query_streaming(
            prompt=prompt,
            tenant_id=tenant_id,
            user_id=user_id,
            tier=tier,
            skill_names=skill_names,
            session_id=session_id,
        ):
            chunks.append(chunk)
            # In Runtime mode, chunks are yielded for streaming
            if chunk.get("type") == "text":
                yield {"type": "text", "data": chunk.get("data", "")}
            elif chunk.get("type") == "tool_use":
                yield {"type": "tool_use", "name": chunk.get("name", ""), "input": chunk.get("input", {})}
            elif chunk.get("type") == "tool_result":
                yield {"type": "tool_result", "name": chunk.get("name", ""), "result": chunk.get("result", {})}
            elif chunk.get("type") in ("complete", "error"):
                yield chunk

    @app.ping
    async def health():
        """Health check for Runtime load balancer."""
        from app.strands_agentic_service import MODEL, SKILL_AGENT_REGISTRY
        return {
            "status": "healthy",
            "service": "EAGLE - NCI Acquisition Assistant",
            "model": MODEL,
            "agents": len(SKILL_AGENT_REGISTRY),
        }

    return app


async def runtime_invoke(
    prompt: str,
    tenant_id: str = "demo-tenant",
    user_id: str = "demo-user",
    tier: str = "advanced",
    session_id: str | None = None,
    skill_names: list[str] | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Invoke the agent through Runtime or locally.

    When running on AgentCore Runtime, routes through the Runtime data plane.
    When running locally, calls sdk_query_streaming directly.
    """
    if _RUNTIME_MODE:
        # On Runtime: invoke via data plane (handled by @app.entrypoint)
        # This path is used when other agents call this agent (A2A)
        try:
            import boto3
            client = boto3.client("bedrock-agentcore", region_name=os.getenv("AWS_REGION", "us-east-1"))
            runtime_id = os.getenv("AGENTCORE_RUNTIME_ID", "")

            response = client.invoke_agent_runtime(
                agentRuntimeIdentifier=runtime_id,
                input=json.dumps({
                    "prompt": prompt,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "tier": tier,
                    "session_id": session_id,
                    "skill_names": skill_names,
                }),
            )

            output = response.get("output", "{}")
            result = json.loads(output) if isinstance(output, str) else output
            yield result

        except Exception as exc:
            logger.error("Runtime invocation failed: %s — falling back to local", exc)
            # Fall through to local execution

    # Local execution (ECS Fargate or development)
    from app.strands_agentic_service import sdk_query_streaming

    async for chunk in sdk_query_streaming(
        prompt=prompt,
        tenant_id=tenant_id,
        user_id=user_id,
        tier=tier,
        skill_names=skill_names,
        session_id=session_id,
    ):
        yield chunk


# Auto-create app when running as Runtime entrypoint
if _RUNTIME_MODE:
    runtime_app = create_runtime_app()

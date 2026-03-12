"""
AgentCore Policy Service — Cedar-based policy enforcement for tier gating.

Replaces the manual TIER_TOOLS dict in strands_agentic_service.py with
Cedar policies enforced at the Gateway level.

When AGENTCORE_POLICY_ENGINE_ID is set, tool access is evaluated against
Cedar policies before execution. Falls back to the TIER_TOOLS dict when
Policy is unavailable.

Policy structure:
    - basic-tier: No tool access (chat only)
    - advanced-tier: workspace_memory, web_search, knowledge_search, knowledge_fetch
    - premium-tier: All tools (adds browse_url, code_execute, Bash)
"""

import logging
import os
from typing import Any

logger = logging.getLogger("eagle.agentcore_policy")

_REGION = os.getenv("AWS_REGION", "us-east-1")
_POLICY_ENGINE_ID = os.getenv("AGENTCORE_POLICY_ENGINE_ID", "")

# Lazy singleton
_policy_client = None

# Fallback tier gating (same as strands_agentic_service.py TIER_TOOLS)
TIER_TOOLS_FALLBACK = {
    "basic": [],
    "advanced": ["Read", "Glob", "Grep", "workspace_memory", "web_search",
                 "knowledge_search", "knowledge_fetch"],
    "premium": ["Read", "Glob", "Grep", "Bash", "workspace_memory", "web_search",
                "browse_url", "code_execute", "knowledge_search", "knowledge_fetch"],
}


def _get_policy_client():
    """Lazy-init policy evaluation client."""
    global _policy_client
    if _policy_client is not None:
        return _policy_client

    if not _POLICY_ENGINE_ID:
        logger.info("AGENTCORE_POLICY_ENGINE_ID not set — using TIER_TOOLS fallback")
        return None

    try:
        import boto3
        _policy_client = boto3.client("bedrock-agentcore-control", region_name=_REGION)
        logger.info("AgentCore Policy client initialized (engine=%s)", _POLICY_ENGINE_ID)
        return _policy_client
    except Exception as exc:
        logger.warning("AgentCore Policy unavailable: %s — using TIER_TOOLS fallback", exc)
        return None


def is_policy_available() -> bool:
    """Check if AgentCore Policy is configured."""
    return _get_policy_client() is not None and bool(_POLICY_ENGINE_ID)


def evaluate_tool_access(
    tool_name: str,
    tenant_id: str,
    user_id: str,
    tier: str,
) -> dict[str, Any]:
    """Evaluate whether a user can access a specific tool.

    Returns:
        {"allowed": bool, "reason": str, "source": "policy"|"fallback"}
    """
    client = _get_policy_client()

    if client:
        return _policy_evaluate(client, tool_name, tenant_id, user_id, tier)
    return _fallback_evaluate(tool_name, tier)


def _policy_evaluate(client, tool_name: str, tenant_id: str, user_id: str, tier: str) -> dict:
    """Evaluate access via AgentCore Cedar Policy."""
    try:
        response = client.evaluate_policy(
            policyEngineIdentifier=_POLICY_ENGINE_ID,
            request={
                "principal": {
                    "entityType": "Eagle::User",
                    "entityId": f"{tenant_id}:{user_id}",
                },
                "action": {
                    "actionType": "Eagle::Action",
                    "actionId": "InvokeTool",
                },
                "resource": {
                    "entityType": "Eagle::Tool",
                    "entityId": tool_name,
                },
                "context": {
                    "tier": tier,
                    "tenant_id": tenant_id,
                },
            },
        )

        decision = response.get("decision", "DENY")
        return {
            "allowed": decision == "ALLOW",
            "reason": response.get("reason", ""),
            "source": "policy",
        }

    except Exception as exc:
        logger.warning("Policy evaluation failed for %s: %s — fallback", tool_name, exc)
        return _fallback_evaluate(tool_name, tier)


def _fallback_evaluate(tool_name: str, tier: str) -> dict:
    """Fallback evaluation using TIER_TOOLS dict."""
    allowed_tools = TIER_TOOLS_FALLBACK.get(tier, [])

    # If tool list is empty for this tier, only allow if tool is a subagent
    # (subagents are always allowed — tier only restricts service tools)
    if not allowed_tools:
        return {
            "allowed": False,
            "reason": f"Tier '{tier}' does not have access to '{tool_name}'",
            "source": "fallback",
        }

    return {
        "allowed": tool_name in allowed_tools,
        "reason": f"Tier '{tier}' {'allows' if tool_name in allowed_tools else 'blocks'} '{tool_name}'",
        "source": "fallback",
    }


def filter_tools_by_policy(
    tools: list,
    tenant_id: str,
    user_id: str,
    tier: str,
) -> list:
    """Filter a list of Strands @tool functions by policy evaluation.

    Used by build_skill_tools() to enforce tier-based access control
    on service tools before passing them to the Strands Agent.
    """
    client = _get_policy_client()

    if not client:
        # Fallback: use TIER_TOOLS dict
        allowed = set(TIER_TOOLS_FALLBACK.get(tier, []))
        if not allowed:
            return []  # basic tier gets no service tools
        return [t for t in tools if _get_tool_name(t) in allowed or _is_subagent(t)]

    # Evaluate each tool against policy
    filtered = []
    for tool_func in tools:
        tool_name = _get_tool_name(tool_func)
        result = evaluate_tool_access(tool_name, tenant_id, user_id, tier)
        if result["allowed"]:
            filtered.append(tool_func)
        else:
            logger.debug("Policy denied tool %s for %s/%s (tier=%s)", tool_name, tenant_id, user_id, tier)

    return filtered


def _get_tool_name(tool_func) -> str:
    """Extract tool name from a Strands @tool function."""
    spec = getattr(tool_func, "tool_spec", None)
    if spec and isinstance(spec, dict):
        return spec.get("name", "")
    return getattr(tool_func, "__name__", "")


def _is_subagent(tool_func) -> bool:
    """Check if a tool function is a subagent (always allowed)."""
    doc = getattr(tool_func, "__doc__", "") or ""
    return "specialist" in doc.lower() or "subagent" in doc.lower()


def get_tier_tools(tier: str) -> list[str]:
    """Get allowed tool names for a tier (fallback-compatible)."""
    if is_policy_available():
        # When Policy is active, tier tools are evaluated dynamically
        return TIER_TOOLS_FALLBACK.get(tier, [])
    return TIER_TOOLS_FALLBACK.get(tier, [])

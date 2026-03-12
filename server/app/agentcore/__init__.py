"""AgentCore — Bedrock AgentCore SDK wrappers for EAGLE.

Submodules: browser, code, gateway, identity, memory, observability, policy, runtime.
"""

from .browser import browse_urls, _strip_html, _fallback_browse, _fetch_url_text
from .code import execute_code
from .gateway import (
    is_gateway_available, list_gateway_tools,
    invoke_gateway_tool, create_gateway_tool_handler,
)
from .identity import is_identity_available, resolve_identity, get_scoped_credentials
from .memory import workspace_memory, batch_write, batch_delete
from .observability import (
    is_observability_enabled, trace_supervisor_query,
    trace_tool_invocation, trace_subagent_delegation,
    record_metric, _NoOpSpan,
)
from .policy import (
    TIER_TOOLS_FALLBACK, is_policy_available,
    evaluate_tool_access, filter_tools_by_policy, get_tier_tools,
)
from .runtime import is_runtime_mode, create_runtime_app, runtime_invoke

__all__ = [
    # browser
    "browse_urls", "_strip_html", "_fallback_browse", "_fetch_url_text",
    # code
    "execute_code",
    # gateway
    "is_gateway_available", "list_gateway_tools",
    "invoke_gateway_tool", "create_gateway_tool_handler",
    # identity
    "is_identity_available", "resolve_identity", "get_scoped_credentials",
    # memory
    "workspace_memory", "batch_write", "batch_delete",
    # observability
    "is_observability_enabled", "trace_supervisor_query",
    "trace_tool_invocation", "trace_subagent_delegation",
    "record_metric", "_NoOpSpan",
    # policy
    "TIER_TOOLS_FALLBACK", "is_policy_available",
    "evaluate_tool_access", "filter_tools_by_policy", "get_tier_tools",
    # runtime
    "is_runtime_mode", "create_runtime_app", "runtime_invoke",
]

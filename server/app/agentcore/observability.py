"""
AgentCore Observability — OTEL-based tracing and metrics via ADOT.

OTEL is always enabled. If the opentelemetry SDK is not installed,
spans degrade to _NoOpSpan (no-crash, no-data). There is no env var
gate — observability is a non-negotiable part of the platform.

This module adds custom spans for:
- Supervisor query lifecycle (setup, execution, streaming)
- Tool invocations with input/output capture
- Subagent delegation with prompt preview
- Session persistence operations
"""

import logging
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger("eagle.agentcore_observability")

# Lazy tracer — initialized once
_tracer = None


def _get_tracer():
    """Get or create the OTEL tracer."""
    global _tracer
    if _tracer is not None:
        return _tracer

    try:
        from opentelemetry import trace
        _tracer = trace.get_tracer(
            "eagle.agent",
            schema_url="https://opentelemetry.io/schemas/1.11.0",
        )
        logger.info("OTEL tracer initialized (eagle.agent)")
        return _tracer
    except ImportError:
        logger.info("OpenTelemetry not installed — observability spans disabled")
        return None
    except Exception as exc:
        logger.warning("OTEL tracer init failed: %s", exc)
        return None


def is_observability_enabled() -> bool:
    """Check if OTEL tracing is available. Always true when SDK is installed."""
    return _get_tracer() is not None


@contextmanager
def trace_supervisor_query(
    tenant_id: str,
    user_id: str,
    tier: str,
    session_id: str = "",
    fast_path: bool = False,
):
    """Context manager for tracing a full supervisor query lifecycle.

    Usage:
        with trace_supervisor_query(tenant_id, user_id, tier) as span:
            span.set_attribute("tools_count", len(tools))
            # ... run agent ...
            span.set_attribute("response_length", len(response))
    """
    tracer = _get_tracer()
    if not tracer:
        yield _NoOpSpan()
        return

    with tracer.start_as_current_span("supervisor_query") as span:
        span.set_attribute("eagle.tenant_id", tenant_id)
        span.set_attribute("eagle.user_id", user_id)
        span.set_attribute("eagle.tier", tier)
        span.set_attribute("eagle.session_id", session_id)
        span.set_attribute("eagle.fast_path", fast_path)
        try:
            yield span
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc))
            raise


@contextmanager
def trace_tool_invocation(
    tool_name: str,
    tenant_id: str = "",
    tool_input_preview: str = "",
):
    """Trace a single tool invocation."""
    tracer = _get_tracer()
    if not tracer:
        yield _NoOpSpan()
        return

    with tracer.start_as_current_span(f"tool.{tool_name}") as span:
        span.set_attribute("eagle.tool.name", tool_name)
        span.set_attribute("eagle.tenant_id", tenant_id)
        if tool_input_preview:
            span.set_attribute("eagle.tool.input_preview", tool_input_preview[:500])
        try:
            yield span
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc))
            raise


@contextmanager
def trace_subagent_delegation(
    agent_name: str,
    tenant_id: str = "",
    query_preview: str = "",
):
    """Trace a subagent delegation."""
    tracer = _get_tracer()
    if not tracer:
        yield _NoOpSpan()
        return

    with tracer.start_as_current_span(f"subagent.{agent_name}") as span:
        span.set_attribute("eagle.subagent.name", agent_name)
        span.set_attribute("eagle.tenant_id", tenant_id)
        if query_preview:
            span.set_attribute("eagle.subagent.query_preview", query_preview[:500])
        try:
            yield span
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc))
            raise


def record_metric(
    name: str,
    value: float,
    attributes: dict[str, Any] | None = None,
):
    """Record a custom metric value.

    Common metrics:
        eagle.ttft_ms — Time to first token
        eagle.total_duration_ms — Full query duration
        eagle.tools_called — Number of tool invocations
        eagle.input_tokens — Token usage
        eagle.output_tokens — Token usage
    """
    try:
        from opentelemetry import metrics
        meter = metrics.get_meter("eagle.agent")

        # Use histogram for duration metrics, counter for counts
        if "duration" in name or "ttft" in name:
            histogram = meter.create_histogram(name, unit="ms")
            histogram.record(value, attributes=attributes or {})
        else:
            counter = meter.create_counter(name)
            counter.add(int(value), attributes=attributes or {})

    except ImportError:
        pass  # OTEL not installed
    except Exception as exc:
        logger.debug("Metric recording failed for %s: %s", name, exc)


class _NoOpSpan:
    """No-op span for when OTEL is not available."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def add_event(self, name: str, attributes: dict | None = None) -> None:
        pass

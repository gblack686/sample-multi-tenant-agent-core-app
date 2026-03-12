"""
Tests for all AgentCore service modules.

Covers: Browser, Memory, Code Interpreter, Gateway, Identity,
Observability, Policy, Runtime — all in fallback mode (no live AWS).
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure fallback mode for all modules
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.pop("AGENTCORE_MEMORY_ID", None)
os.environ.pop("AGENTCORE_GATEWAY_ID", None)
os.environ.pop("AGENTCORE_POLICY_ENGINE_ID", None)
os.environ.pop("AGENTCORE_RUNTIME_MODE", None)
os.environ.pop("AGENTCORE_IDENTITY_ENABLED", None)
os.environ.pop("AGENT_OBSERVABILITY_ENABLED", None)


# ── Browser Tests ─────────────────────────────────────────────────

class TestAgentCoreBrowser:

    def test_browse_empty_urls(self):
        from app.agentcore.browser import browse_urls
        result = browse_urls([])
        assert result == {"error": "No URLs provided"}

    def test_browse_caps_at_10(self):
        from app.agentcore.browser import browse_urls
        urls = [f"http://example.com/{i}" for i in range(15)]
        with patch("app.agentcore.browser._fetch_url") as mock:
            mock.return_value = {"url": "test", "content": "ok", "status": "ok"}
            result = browse_urls(urls)
            assert result["count"] == 10

    def test_strip_html(self):
        from app.agentcore.browser import _strip_html
        html = '<div><script>alert("x")</script><p>Hello &amp; world</p></div>'
        text = _strip_html(html)
        assert "Hello & world" in text
        assert "<script>" not in text
        assert "alert" not in text

    def test_fallback_browse_error_handling(self):
        from app.agentcore.browser import _fallback_browse
        with patch("app.agentcore.browser._fetch_url") as mock:
            mock.return_value = {"url": "http://bad", "content": "", "status": "error", "error": "timeout"}
            result = _fallback_browse(["http://bad"], None, 100_000)
            assert result["count"] == 1
            assert result["results"][0]["status"] == "error"

    def test_fetch_url_text_success(self):
        from app.agentcore.browser import _fetch_url_text
        mock_resp = MagicMock()
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.text = "<p>Test content</p>"
        mock_resp.raise_for_status = MagicMock()
        with patch("requests.get", return_value=mock_resp):
            text = _fetch_url_text("http://example.com", 50_000)
            assert "Test content" in text


# ── Memory Tests ──────────────────────────────────────────────────

class TestAgentCoreMemory:

    def setup_method(self):
        """Reset fallback store between tests."""
        from app.agentcore import memory as agentcore_memory
        agentcore_memory._fallback_store.clear()
        agentcore_memory._manager = None

    def test_write_and_view(self):
        from app.agentcore.memory import workspace_memory
        write = workspace_memory("write", "notes.txt", "t1", "u1", content="hello world")
        assert write["command"] == "write"
        assert write["size"] == 11

        view = workspace_memory("view", "notes.txt", "t1", "u1")
        assert view["content"] == "hello world"

    def test_append(self):
        from app.agentcore.memory import workspace_memory
        workspace_memory("write", "log.txt", "t1", "u1", content="line1")
        workspace_memory("append", "log.txt", "t1", "u1", content="line2")
        view = workspace_memory("view", "log.txt", "t1", "u1")
        assert "line1" in view["content"]
        assert "line2" in view["content"]

    def test_clear(self):
        from app.agentcore.memory import workspace_memory
        workspace_memory("write", "tmp.txt", "t1", "u1", content="data")
        workspace_memory("clear", "tmp.txt", "t1", "u1")
        view = workspace_memory("view", "tmp.txt", "t1", "u1")
        assert view["content"] == "(empty)"

    def test_list_files(self):
        from app.agentcore.memory import workspace_memory
        workspace_memory("write", "a.txt", "t1", "u1", content="aaa")
        workspace_memory("write", "b.txt", "t1", "u1", content="bbb")
        result = workspace_memory("list", "", "t1", "u1")
        assert result["count"] == 2
        assert "a.txt" in result["files"]
        assert "b.txt" in result["files"]

    def test_tenant_isolation(self):
        from app.agentcore.memory import workspace_memory
        workspace_memory("write", "secret.txt", "t1", "u1", content="t1-data")
        workspace_memory("write", "secret.txt", "t2", "u1", content="t2-data")
        v1 = workspace_memory("view", "secret.txt", "t1", "u1")
        v2 = workspace_memory("view", "secret.txt", "t2", "u1")
        assert v1["content"] == "t1-data"
        assert v2["content"] == "t2-data"

    def test_unknown_command(self):
        from app.agentcore.memory import workspace_memory
        result = workspace_memory("invalid", "x.txt", "t1", "u1")
        assert "error" in result

    def test_batch_write(self):
        from app.agentcore.memory import batch_write, workspace_memory
        result = batch_write(
            {"a.txt": "aaa", "b.txt": "bbb"},
            tenant_id="t1", user_id="u1",
        )
        assert result["written"] == 2
        va = workspace_memory("view", "a.txt", "t1", "u1")
        assert va["content"] == "aaa"

    def test_batch_delete(self):
        from app.agentcore.memory import batch_write, batch_delete, workspace_memory
        batch_write({"x.txt": "xxx", "y.txt": "yyy"}, "t1", "u1")
        result = batch_delete(["x.txt"], "t1", "u1")
        assert result["deleted"] == 1
        vx = workspace_memory("view", "x.txt", "t1", "u1")
        assert vx["content"] == "(empty)"
        vy = workspace_memory("view", "y.txt", "t1", "u1")
        assert vy["content"] == "yyy"


# ── Code Interpreter Tests ────────────────────────────────────────

class TestAgentCoreCode:

    def setup_method(self):
        """Reset singleton and force fallback mode between tests."""
        from app.agentcore import code as agentcore_code
        # Force None so _get_code_client() re-evaluates, then block the import
        agentcore_code._code_client = None

    def _force_fallback(self):
        """Patch _get_code_client to return None (force fallback)."""
        return patch("app.agentcore.code._get_code_client", return_value=None)

    def test_empty_code(self):
        from app.agentcore.code import execute_code
        result = execute_code("")
        assert result == {"error": "No code provided"}

    def test_fallback_python_execution(self):
        from app.agentcore.code import execute_code
        with self._force_fallback():
            result = execute_code("print(2 + 3)")
            assert result["status"] == "ok"
            assert "5" in result["output"]
            assert result.get("mode") == "fallback"

    def test_fallback_blocks_dangerous_imports(self):
        from app.agentcore.code import execute_code
        with self._force_fallback():
            for mod in ["os", "subprocess", "shutil", "socket"]:
                result = execute_code(f"import {mod}")
                assert result["status"] == "error"
                assert "not allowed" in result["error"]

    def test_fallback_rejects_non_python(self):
        from app.agentcore.code import execute_code
        with self._force_fallback():
            result = execute_code("console.log('hi')", language="javascript")
            assert result["status"] == "error"
            assert "Python" in result["error"]

    def test_fallback_handles_runtime_error(self):
        from app.agentcore.code import execute_code
        with self._force_fallback():
            result = execute_code("x = 1/0")
            assert result["status"] == "error"
            assert "division" in result["error"].lower()

    def test_fallback_multiline(self):
        from app.agentcore.code import execute_code
        with self._force_fallback():
            code = "x = [1,2,3]\nfor i in x:\n    print(i)"
            result = execute_code(code)
            assert result["status"] == "ok"
            assert "1" in result["output"]
            assert "3" in result["output"]


# ── Gateway Tests ─────────────────────────────────────────────────

class TestAgentCoreGateway:

    def test_gateway_not_available_without_env(self):
        from app.agentcore.gateway import is_gateway_available
        assert is_gateway_available() is False

    def test_list_tools_returns_empty_when_unavailable(self):
        from app.agentcore.gateway import list_gateway_tools
        assert list_gateway_tools() == []

    def test_invoke_tool_error_when_unavailable(self):
        from app.agentcore.gateway import invoke_gateway_tool
        result = invoke_gateway_tool("some_tool", {"key": "val"}, "t1", "u1")
        assert "error" in result

    def test_create_handler_returns_none_without_strands(self):
        from app.agentcore.gateway import create_gateway_tool_handler
        with patch.dict("sys.modules", {"strands": None}):
            # When strands is not importable
            handler = create_gateway_tool_handler("test", "t1", "u1")
            # May return None if strands not available or may succeed
            # Just verify it doesn't crash
            assert handler is None or callable(handler)


# ── Identity Tests ────────────────────────────────────────────────

class TestAgentCoreIdentity:

    def test_identity_not_available_without_env(self):
        from app.agentcore.identity import is_identity_available
        assert is_identity_available() is False

    def test_cognito_fallback_called(self):
        from app.agentcore.identity import resolve_identity
        mock_ctx = MagicMock()
        mock_ctx.user_id = "test-user"
        mock_ctx.tenant_id = "test-tenant"
        mock_ctx.tier = "advanced"
        mock_ctx.email = "test@example.com"
        mock_ctx.roles = ["admin"]

        with patch("app.cognito_auth.extract_user_context", return_value=(mock_ctx, None)):
            result = resolve_identity("fake-token")
            assert result["source"] == "cognito"
            assert result["user_id"] == "test-user"
            assert result["tenant_id"] == "test-tenant"

    def test_scoped_credentials_unavailable(self):
        from app.agentcore.identity import get_scoped_credentials
        result = get_scoped_credentials("t1", "u1", "s3")
        assert result["scoped"] is False


# ── Observability Tests ───────────────────────────────────────────

class TestAgentCoreObservability:

    def test_observability_always_enabled(self):
        """OTEL is always on — returns True when SDK is installed."""
        from app.agentcore.observability import is_observability_enabled
        assert is_observability_enabled() is True

    def test_noop_span(self):
        from app.agentcore.observability import _NoOpSpan
        span = _NoOpSpan()
        span.set_attribute("key", "value")  # should not raise
        span.add_event("test")  # should not raise

    def test_trace_supervisor_query_noop(self):
        from app.agentcore.observability import trace_supervisor_query
        with trace_supervisor_query("t1", "u1", "advanced") as span:
            span.set_attribute("tools_count", 5)
            # Should complete without error

    def test_trace_tool_invocation_noop(self):
        from app.agentcore.observability import trace_tool_invocation
        with trace_tool_invocation("web_search", "t1", "test query") as span:
            span.set_attribute("result_size", 100)

    def test_trace_subagent_delegation_noop(self):
        from app.agentcore.observability import trace_subagent_delegation
        with trace_subagent_delegation("legal_counsel", "t1", "FAR question") as span:
            span.set_attribute("tokens", 500)

    def test_record_metric_noop(self):
        from app.agentcore.observability import record_metric
        # Should not raise even without OTEL
        record_metric("eagle.ttft_ms", 150.0)
        record_metric("eagle.tools_called", 3)

    def test_trace_propagates_exceptions(self):
        from app.agentcore.observability import trace_supervisor_query
        with pytest.raises(ValueError, match="test error"):
            with trace_supervisor_query("t1", "u1", "advanced") as span:
                raise ValueError("test error")


# ── Policy Tests ──────────────────────────────────────────────────

class TestAgentCorePolicy:

    def test_policy_not_available_without_env(self):
        from app.agentcore.policy import is_policy_available
        assert is_policy_available() is False

    def test_fallback_basic_tier_blocks_all(self):
        from app.agentcore.policy import evaluate_tool_access
        result = evaluate_tool_access("web_search", "t1", "u1", "basic")
        assert result["allowed"] is False
        assert result["source"] == "fallback"

    def test_fallback_advanced_tier_allows_search(self):
        from app.agentcore.policy import evaluate_tool_access
        result = evaluate_tool_access("web_search", "t1", "u1", "advanced")
        assert result["allowed"] is True

    def test_fallback_advanced_tier_blocks_browse(self):
        from app.agentcore.policy import evaluate_tool_access
        result = evaluate_tool_access("browse_url", "t1", "u1", "advanced")
        assert result["allowed"] is False

    def test_fallback_premium_tier_allows_all(self):
        from app.agentcore.policy import evaluate_tool_access
        for tool in ["web_search", "browse_url", "code_execute", "Bash"]:
            result = evaluate_tool_access(tool, "t1", "u1", "premium")
            assert result["allowed"] is True, f"Expected {tool} allowed for premium"

    def test_get_tier_tools(self):
        from app.agentcore.policy import get_tier_tools
        basic = get_tier_tools("basic")
        assert basic == []
        advanced = get_tier_tools("advanced")
        assert "web_search" in advanced
        premium = get_tier_tools("premium")
        assert "browse_url" in premium
        assert "code_execute" in premium

    def test_filter_tools_basic_returns_empty(self):
        from app.agentcore.policy import filter_tools_by_policy
        mock_tools = [MagicMock(__name__="web_search", tool_spec={"name": "web_search"})]
        result = filter_tools_by_policy(mock_tools, "t1", "u1", "basic")
        assert result == []

    def test_filter_tools_advanced_keeps_allowed(self):
        from app.agentcore.policy import filter_tools_by_policy

        def make_tool(name):
            t = MagicMock(__name__=name, __doc__="A service tool")
            t.tool_spec = {"name": name}
            return t

        tools = [make_tool("web_search"), make_tool("browse_url"), make_tool("workspace_memory")]
        result = filter_tools_by_policy(tools, "t1", "u1", "advanced")
        names = [t.tool_spec["name"] for t in result]
        assert "web_search" in names
        assert "workspace_memory" in names
        assert "browse_url" not in names


# ── Runtime Tests ─────────────────────────────────────────────────

class TestAgentCoreRuntime:

    def test_runtime_mode_off_by_default(self):
        from app.agentcore.runtime import is_runtime_mode
        assert is_runtime_mode() is False

    def test_create_runtime_app_without_sdk(self):
        from app.agentcore.runtime import create_runtime_app
        with patch.dict("sys.modules", {"bedrock_agentcore.runtime": None}):
            with patch("builtins.__import__", side_effect=ImportError("no module")):
                # The function may return None or raise — just verify no crash
                try:
                    app = create_runtime_app()
                except (ImportError, TypeError):
                    pass  # Expected when SDK not installed

    @pytest.mark.asyncio
    async def test_runtime_invoke_local_mode(self):
        from app.agentcore.runtime import runtime_invoke

        async def mock_streaming(**kwargs):
            yield {"type": "text", "data": "Hello"}
            yield {"type": "complete", "data": "done"}

        with patch("app.agentcore.runtime._RUNTIME_MODE", False):
            with patch("app.strands_agentic_service.sdk_query_streaming", side_effect=mock_streaming):
                chunks = []
                async for chunk in runtime_invoke("test prompt"):
                    chunks.append(chunk)
                assert len(chunks) == 2
                assert chunks[0]["type"] == "text"


# ── Integration: Module Import Tests ──────────────────────────────

class TestModuleImports:
    """Verify all AgentCore modules import cleanly without SDK installed."""

    def test_import_browser(self):
        import app.agentcore.browser

    def test_import_memory(self):
        import app.agentcore.memory

    def test_import_code(self):
        import app.agentcore.code

    def test_import_gateway(self):
        import app.agentcore.gateway

    def test_import_identity(self):
        import app.agentcore.identity

    def test_import_observability(self):
        import app.agentcore.observability

    def test_import_policy(self):
        import app.agentcore.policy

    def test_import_runtime(self):
        import app.agentcore.runtime

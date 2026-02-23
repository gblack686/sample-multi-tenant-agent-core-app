"""
Streaming Routes for EAGLE NCI Acquisition Assistant

Provides SSE (Server-Sent Events) streaming chat and health check endpoints.
Updated to use EAGLE's agentic_service.stream_chat() with Anthropic SDK
instead of the original Bedrock Agent wrapper.

# NOTE: main.py should include this router:
#   from app.streaming_routes import create_streaming_router
#   streaming_router = create_streaming_router(store, subscription_service)
#   app.include_router(streaming_router)
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional

from .cognito_auth import extract_user_context, UserContext
from .stream_protocol import StreamEvent, StreamEventType, MultiAgentStreamWriter
from .models import ChatMessage
from .dynamodb_store import DynamoDBStore
from .subscription_service import SubscriptionService
from .agentic_service import stream_chat, MODEL, EAGLE_TOOLS

import os
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
USE_SDK_BACKEND = os.getenv("USE_SDK_BACKEND", "true").lower() == "true"

logger = logging.getLogger(__name__)


async def stream_generator(
    message: str,
    tenant_id: str,
    user_id: str,
    session_id: str,
    tier,
    store: DynamoDBStore,
    subscription_service: SubscriptionService,
) -> AsyncGenerator[str, None]:
    """Generate SSE events using EAGLE's Anthropic SDK streaming.

    The flow is:
      1. Yield a metadata event with agent info (initial connection handshake).
      2. Call agentic_service.stream_chat() with SSE-mapping callbacks.
      3. on_text callbacks → TEXT SSE events (real-time streaming).
      4. on_tool_use callbacks → TOOL_USE SSE events.
      5. on_tool_result callbacks → TOOL_RESULT SSE events.
      6. Yield a COMPLETE event on success, or an ERROR event on failure.
    """
    writer = MultiAgentStreamWriter("eagle", "EAGLE Acquisition Assistant")
    queue: asyncio.Queue[str] = asyncio.Queue()

    try:
        # Build messages list with just the current message
        # (In a full implementation, you'd load conversation history here)
        messages = [{"role": "user", "content": message}]

        # Define SSE-mapping callbacks
        async def on_text(delta: str):
            await writer.write_text(queue, delta)

        async def on_tool_use(tool_name: str, tool_input: dict):
            await writer.write_tool_use(queue, tool_name, tool_input)

        async def on_tool_result(tool_name: str, output: str):
            # Truncate large tool results for SSE display
            display_output = output[:2000] + "..." if len(output) > 2000 else output
            await writer.write_tool_result(queue, tool_name, display_output)

        async def on_agent_status(agent_name: str, message_text: str, status: str):
            await writer.write_agent_status(queue, agent_name, message_text, status)

        # Trace context for telemetry persistence
        trace_context = {
            "tenant_id": tenant_id,
            "user_id": user_id,
        }

        # Stream chat using EAGLE's Anthropic SDK
        result = await stream_chat(
            messages,
            on_text=on_text,
            on_tool_use=on_tool_use,
            on_tool_result=on_tool_result,
            on_agent_status=on_agent_status,
            session_id=session_id,
            trace_context=trace_context,
        )

        # Drain all queued events
        while not queue.empty():
            yield await queue.get()

        # Signal completion
        await writer.write_complete(queue)
        yield await queue.get()

        # Persist telemetry (never break the SSE stream)
        try:
            collector = result.get("trace_collector")
            if collector:
                summary = collector.summary()
                spans = collector.get_completed_spans()

                from .telemetry.trace_store import store_trace
                store_trace(summary=summary, spans=spans, trace_json=collector.to_trace_json())

                from .telemetry.cloudwatch_emitter import emit_trace_completed
                emit_trace_completed(summary)
        except Exception as te:
            logger.warning("Failed to persist telemetry (SSE): %s", te)

    except Exception as e:
        logger.error("Streaming chat error: %s", str(e), exc_info=True)
        await writer.write_error(queue, str(e))
        yield await queue.get()


async def stream_generator_sdk(
    message: str,
    tenant_id: str,
    user_id: str,
    session_id: str,
    tier,
    store: DynamoDBStore,
    subscription_service: SubscriptionService,
) -> AsyncGenerator[str, None]:
    """Generate SSE events from the Claude Agent SDK path.

    Consumes sdk_query() async generator, maps SDK message types
    to SSE events via MultiAgentStreamWriter. Produces rich telemetry
    with spans, tool timing, and subagent tracking.

    Telemetry persistence is handled internally by sdk_query() after
    the generator is fully consumed — no persistence code needed here.
    """
    from .sdk_agentic_service import sdk_query

    writer = MultiAgentStreamWriter("eagle", "EAGLE Acquisition Assistant")
    queue: asyncio.Queue[str] = asyncio.Queue()

    try:
        # on_status callback: SpanTracker hooks call this during iteration.
        # Events land in the queue and get drained after each SDK message.
        async def on_status(agent_name: str, message_text: str, status: str):
            await writer.write_agent_status(queue, agent_name, message_text, status)

        # Track tool_use_id → tool_name for resolving ToolResultBlock names
        tool_id_to_name: dict[str, str] = {}

        async for msg in sdk_query(
            prompt=message,
            tenant_id=tenant_id,
            user_id=user_id,
            tier=tier,
            session_id=session_id,
            on_status=on_status,
        ):
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage":
                if hasattr(msg, "content") and msg.content:
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "TextBlock":
                            text = getattr(block, "text", "")
                            if text:
                                await writer.write_text(queue, text)
                        elif block_type == "ThinkingBlock":
                            thinking = getattr(block, "thinking", getattr(block, "text", ""))
                            if thinking:
                                await writer.write_reasoning(queue, thinking)
                        elif block_type == "ToolUseBlock":
                            tool_name = getattr(block, "name", "unknown")
                            tool_input = getattr(block, "input", {})
                            tool_id = getattr(block, "id", "")
                            if tool_id:
                                tool_id_to_name[tool_id] = tool_name
                            await writer.write_tool_use(queue, tool_name, tool_input)

            elif msg_type == "UserMessage":
                if hasattr(msg, "content") and msg.content:
                    for block in msg.content:
                        block_type = type(block).__name__
                        if block_type == "ToolResultBlock":
                            tool_id = getattr(block, "tool_use_id", "")
                            tool_name = tool_id_to_name.get(tool_id, tool_id)
                            content = getattr(block, "content", "")
                            display = str(content)[:2000] if content else ""
                            await writer.write_tool_result(queue, tool_name, display)

            elif msg_type == "ResultMessage":
                # ResultMessage.result contains the final text output.
                # When the supervisor delegates via Task tool, this is where
                # the synthesized answer lives (not in AssistantMessage).
                result_text = getattr(msg, "result", "")
                if result_text:
                    await writer.write_text(queue, result_text)

            # Drain all queued events (includes on_status events from hooks)
            while not queue.empty():
                yield await queue.get()

        # Generator exhausted — sdk_query() has already persisted telemetry
        await writer.write_complete(queue)
        yield await queue.get()

    except Exception as e:
        logger.error("SDK streaming error: %s", str(e), exc_info=True)
        await writer.write_error(queue, str(e))
        yield await queue.get()


def create_streaming_router(
    store: DynamoDBStore,
    subscription_service: SubscriptionService,
) -> APIRouter:
    """Factory to create router with service dependencies.

    This pattern allows main.py to wire up concrete service instances::

        streaming_router = create_streaming_router(store, subscription_service)
        app.include_router(streaming_router)

    Parameters
    ----------
    store : DynamoDBStore
        The initialised DynamoDB store.
    subscription_service : SubscriptionService
        The initialised subscription/usage service.

    Returns
    -------
    APIRouter
        A FastAPI router containing the /api/chat/stream and
        /api/health endpoints.
    """
    router = APIRouter()

    # ------------------------------------------------------------------
    # POST /api/chat/stream - Streaming chat via SSE (EAGLE backend)
    # ------------------------------------------------------------------
    @router.post("/api/chat/stream")
    async def chat_stream(
        message: ChatMessage,
        authorization: Optional[str] = Header(None),
    ):
        """Send message to EAGLE agent and receive a streaming SSE response.

        Uses EAGLE cognito_auth (DEV_MODE-aware). Accepts the same request
        body as POST /api/chat. The response is delivered as a stream of
        text/event-stream SSE events following the StreamEvent protocol.
        """
        # Authenticate using EAGLE cognito_auth (supports DEV_MODE bypass)
        user, error = extract_user_context(authorization)
        if REQUIRE_AUTH and user.user_id == "anonymous":
            raise HTTPException(status_code=401, detail=error or "Authentication required")

        tenant_id = user.tenant_id
        user_id = user.user_id

        # Use tenant_context from message body if provided, else from auth
        if message.tenant_context:
            tenant_id = message.tenant_context.tenant_id or tenant_id
            user_id = message.tenant_context.user_id or user_id

        # Build session_id from tenant context or request body
        session_id = message.session_id
        if not session_id:
            if message.tenant_context:
                session_id = f"{tenant_id}-{user_id}-{message.tenant_context.session_id}"
            else:
                import uuid
                session_id = f"{tenant_id}-{user_id}-{uuid.uuid4()}"

        # Select SDK or direct API backend
        use_sdk = message.use_sdk if message.use_sdk is not None else USE_SDK_BACKEND
        generator = stream_generator_sdk if use_sdk else stream_generator

        # Return streaming response
        return StreamingResponse(
            generator(
                message=message.message,
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                tier=user.tier,
                store=store,
                subscription_service=subscription_service,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ------------------------------------------------------------------
    # GET /api/health - Health check (no auth required)
    # ------------------------------------------------------------------
    @router.get("/api/health")
    async def health_check():
        """Return service health status, available agents, and EAGLE tools.

        This endpoint does not require authentication and is intended
        for load-balancer health probes and operational dashboards.
        """
        return {
            "status": "healthy",
            "service": "EAGLE – NCI Acquisition Assistant",
            "version": "4.0.0",
            "model": MODEL,
            "services": {
                "anthropic": True,
                "dynamodb": True,
                "cognito": True,
                "s3": True,
            },
            "agents": [
                {
                    "id": "eagle",
                    "name": "EAGLE Acquisition Assistant",
                    "status": "online",
                },
                {
                    "id": "supervisor",
                    "name": "Supervisor",
                    "status": "online",
                },
                {
                    "id": "oa-intake",
                    "name": "OA Intake Agent",
                    "status": "online",
                },
            ],
            "tools": [tool["name"] for tool in EAGLE_TOOLS],
            "features": {
                "persistent_sessions": os.getenv("USE_PERSISTENT_SESSIONS", "true").lower() == "true",
                "auth_required": os.getenv("REQUIRE_AUTH", "false").lower() == "true",
                "dev_mode": os.getenv("DEV_MODE", "false").lower() == "true",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return router

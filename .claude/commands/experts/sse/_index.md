---
type: expert-file
file-type: index
domain: sse
tags: [expert, sse, streaming, tool-use, tool-result, event-stream, observability]
---

# SSE Expert

> EAGLE Server-Sent Events specialist for streaming protocol, tool observability, event parsing, and frontend event consumption.

## Domain Scope

This expert covers:
- **Stream Protocol** - `server/app/stream_protocol.py` — `StreamEvent`, `MultiAgentStreamWriter`, SSE event types
- **Streaming Routes** - `server/app/streaming_routes.py` — SSE endpoint, event dispatching, tool_result forwarding
- **Callback Handler** - `server/app/strands_agentic_service.py` — `QueueCallbackHandler`, `chunk_queue`, `result_queue`
- **Tool Result Emission** - Factory tools (`_make_*_tool`), `_make_service_tool`, `_make_subagent_tool` — `_emit_tool_result()`
- **Frontend Parsing** - `client/types/stream.ts` — `StreamEvent`, `ToolUse`, `ToolResult` types
- **Frontend Consumer** - `client/hooks/use-agent-stream.ts` — SSE reader, `processEventData()`, `ServerToolResult` accumulation
- **Tool Card UI** - `client/components/chat-simple/tool-use-display.tsx` — `canExpand`, chevron, result rendering
- **State Merge** - `client/components/chat-simple/simple-chat-interface.tsx` — `onComplete` result merge into `toolCallsByMsg`

## Available Commands

| Command | Purpose |
|---------|---------|
| `/experts:sse:question` | Answer SSE/streaming questions without coding |
| `/experts:sse:plan` | Plan SSE or streaming changes using expertise context |
| `/experts:sse:self-improve` | Update expertise after implementations |
| `/experts:sse:plan_build_improve` | Full ACT-LEARN-REUSE workflow |
| `/experts:sse:maintenance` | Validate SSE pipeline health end-to-end |

## Key Files

| File | Purpose |
|------|---------|
| `expertise.md` | Complete mental model for SSE domain |
| `question.md` | Query command for read-only questions |
| `plan.md` | Planning command for SSE changes |
| `self-improve.md` | Expertise update command |
| `plan_build_improve.md` | Full workflow command |
| `maintenance.md` | Validation and health check command |

## Architecture

```
Backend (Python)                              Frontend (TypeScript)
─────────────────                             ────────────────────
Strands Agent (thread)                        use-agent-stream.ts
  │                                             │
  ├─ QueueCallbackHandler                       ├─ fetch('/api/invoke')
  │   ├─ text → chunk_queue                     │   └─ ReadableStream
  │   └─ current_tool_use → chunk_queue         │
  │       (type: tool_use, name, input, id)     ├─ processEventData(line)
  │                                             │   ├─ text → accumulatedText
  ├─ Tool execution (sync in thread)            │   ├─ tool_use → onToolUse()
  │   ├─ _make_service_tool                     │   ├─ tool_result → serverToolResults[]
  │   │   └─ result_queue.put_nowait(           │   └─ complete → onComplete()
  │   │       {tool_result, name, result})      │
  │   ├─ _make_subagent_tool                    ├─ onComplete(serverToolResults)
  │   │   └─ result_queue.put_nowait(           │   └─ merge into toolCallsByMsg
  │   │       {tool_result, name, report})      │       by name (FIFO)
  │   └─ _make_*_tool (factories)               │
  │       └─ _emit_tool_result()                └─ tool-use-display.tsx
  │           └─ result_queue.put_nowait()           ├─ canExpand = status + result
  │                                                  ├─ chevron ▾ when canExpand
sdk_query_streaming()                                └─ expanded: JSON or markdown
  │
  ├─ poll chunk_queue → yield chunks
  ├─ _drain_tool_results() → yield tool_result
  └─ yield {complete, text, tools_called, usage}
       │
streaming_routes.py
  │
  ├─ stream_generator(async gen)
  │   ├─ text → writer.write_text()
  │   ├─ tool_use → writer.write_tool_use(name, input, id)
  │   ├─ tool_result → writer.write_tool_result(name, result)
  │   └─ complete → writer.write_complete()
  │
  └─ SSE: "data: {json}\n\n"
```

## SSE Event Types

| Type | Backend Origin | Frontend Handler | UI Effect |
|------|---------------|-----------------|-----------|
| `text` | `QueueCallbackHandler` data kwarg | `accumulatedText` → `onMessage` | Streaming text bubble |
| `tool_use` | `QueueCallbackHandler` current_tool_use | `onToolUse` → tool card (pending) | Tool card appears |
| `tool_result` | `result_queue` via `_drain_tool_results` | `serverToolResults[]` → `onComplete` merge | Chevron + expandable result |
| `complete` | End of `sdk_query_streaming` | `onComplete(toolResults)` | Finalize message + merge results |
| `error` | Exception handler | `onError` | Error display |

## ACT-LEARN-REUSE Pattern

```
ACT    ->  Modify streaming, add event types, fix tool observability
LEARN  ->  Update expertise.md with patterns and issues
REUSE  ->  Apply patterns to future SSE development
```

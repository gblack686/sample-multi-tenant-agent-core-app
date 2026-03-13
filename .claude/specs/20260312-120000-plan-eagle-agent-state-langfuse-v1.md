# Plan: EAGLE Unified Agent State + Langfuse Telemetry

**ID**: 20260312-120000-plan-eagle-agent-state-langfuse-v1
**Created**: 2026-03-12
**Status**: Ready for Implementation
**Type**: Feature / Enhancement
**Complexity**: Medium

---

## Task Description

Wire the EAGLE unified state schema (4 state_types: `document_ready`, `checklist_update`, `phase_change`, `compliance_alert`) into Strands `agent_state` on the supervisor. Persist state across turns via DynamoDB so each request rehydrates where the previous turn left off. Surface key state fields in Langfuse via `trace_attributes`. Emit structured `agent.state_flush` events to CloudWatch on every turn for operational visibility. Include the final state snapshot in the `complete` SSE event so the frontend syncs without a separate poll.

---

## Objective

After this plan is complete:
1. The supervisor `Agent()` receives a rehydrated `agent_state` dict on every request — no more stateless fresh starts
2. State is flushed back to DynamoDB after every supervisor turn via `AfterInvocationEvent`
3. Langfuse traces show `eagle.phase`, `eagle.docs_completed`, `eagle.docs_required`, `eagle.package_id` as span attributes
4. The `update_state` tool writes into `agent_state` (in addition to pushing SSE metadata) so subagents' updates survive the turn
5. CloudWatch receives a structured `agent.state_flush` event after every turn — queryable via Insights for funnel analysis
6. The `complete` SSE event carries the final `agent_state` snapshot so `use-package-state.ts` stays in sync on every turn

---

## Problem Statement

Currently:
- The supervisor `Agent()` is created **fresh per HTTP request** with no `agent_state` — each turn starts blind
- `update_state` writes to `invocation_state["_sse_metadata"]` which only lives for the duration of a single request
- `document_agent.py:_load_state_snapshot()` looks for `STATE#` messages in DynamoDB but **the writer was never implemented**
- Langfuse traces only carry `eagle.tenant_id`, `eagle.user_id`, `eagle.tier`, `eagle.session_id` — no acquisition context
- There is no way to query Langfuse to see "how many turns did it take to complete an SOW?" or "which sessions stalled at intake?"

---

## Solution Approach

### The Canonical State Schema

Derived from `client/tests/validate-state-push-metadata.spec.ts` (PR #7):

```python
# EagleAgentState — JSON-serializable, passed as agent_state= to supervisor Agent()
{
    # Acquisition lifecycle
    "phase": "intake",                  # intake | analysis | drafting | review | complete
    "previous_phase": None,             # last phase before current

    # Package linkage
    "package_id": None,                 # PKG-YYYY-NNNN or None

    # Document tracking (mirrors package checklist)
    "required_documents": [],           # ["sow", "igce", "market_research", ...]
    "completed_documents": [],          # subset of required that are done
    "document_versions": {},            # { doc_type: { document_id, version, s3_key } }

    # Compliance
    "compliance_alerts": [],            # [{ severity, items: [{name, note}] }]

    # Turn metadata
    "turn_count": 0,
    "last_updated": None,               # ISO-8601
    "session_id": None,                 # echo back for traceability
}
```

### Persistence Pattern

```
DynamoDB eagle table
  PK: SESSION#{tenant_id}#{user_id}
  SK: STATE#{session_id}          ← new SK pattern (existing reader in document_agent.py)
  content: json.dumps(state_dict)
  updated_at: ISO-8601
  ttl: epoch + SESSION_TTL_DAYS
```

### Hook Architecture

Add `AfterInvocationEvent` callback to `EagleSSEHookProvider` (already has `AfterToolCallEvent`):
- Reads `event.agent.state` (the dict Strands maintains on the Agent instance)
- Merges any updates accumulated by tools during the turn
- Saves to DynamoDB via new `save_agent_state()`
- Enriches `trace_attributes` is not directly patchable post-creation, so key fields are logged at `INFO` level with structured JSON for CloudWatch — Langfuse already picks them up via OTEL span attributes set at supervisor construction

### Langfuse Enrichment

`trace_attributes` is set at `Agent()` construction. Since state is loaded before the Agent is created, we can pass it directly:

```python
trace_attributes={
    "eagle.tenant_id": tenant_id,
    "eagle.user_id": user_id,
    "eagle.tier": tier,
    "eagle.session_id": session_id or "",
    # State fields — populated from rehydrated agent_state
    "eagle.phase": agent_state.get("phase", "intake"),
    "eagle.package_id": agent_state.get("package_id") or "",
    "eagle.docs_required": len(agent_state.get("required_documents", [])),
    "eagle.docs_completed": len(agent_state.get("completed_documents", [])),
    "eagle.turn_count": agent_state.get("turn_count", 0),
}
```

---

## Relevant Files

- **`server/app/eagle_state.py`** *(new)* — canonical state module: `_DEFAULTS`, `normalize()`, `apply_event()`, `to_trace_attrs()`, `to_cw_payload()`. **Only file that needs editing when the state schema changes.**
- **`server/app/strands_agentic_service.py`** — remove inline state logic; import from `eagle_state`; wire `AfterInvocationEvent` in `EagleSSEHookProvider`; pass `agent_state=` and `trace_attributes=` in `sdk_query` + `sdk_query_streaming`; include state in `complete` SSE event
- **`server/app/stores/session_store.py`** — add `load_agent_state()` and `save_agent_state()` using `STATE#` SK
- **`server/app/telemetry/cloudwatch_emitter.py`** — add `emit_agent_state_flush()` using `to_cw_payload()` from `eagle_state`
- **`server/app/document_agent.py`** — `_load_state_snapshot()` already reads `STATE#` messages; no change needed once writer is implemented
- **`server/app/main.py`** — Langfuse OTEL already wired (`_setup_langfuse()`), no change
- **`server/requirements.txt`** — `langfuse>=3.0.0` and `strands-agents[otel]>=1.0.0` already present, no change

### New Files
- `server/app/eagle_state.py` — state module (Step 0)

---

## Implementation Phases

### Phase 0: State Module (prerequisite)
Create `eagle_state.py` — the single file that owns the schema, mutations, and read projections. All subsequent phases import from it instead of hardcoding field names.

### Phase 1: State Schema + DynamoDB Read/Write
Implement `load_agent_state` / `save_agent_state` in `session_store.py` using the `STATE#` SK pattern.

### Phase 2: Hook Integration
Add `AfterInvocationEvent` to `EagleSSEHookProvider`; update `sdk_query` and `sdk_query_streaming` to load + pass state.

### Phase 3: Tool Integration + Langfuse Enrichment
Update `update_state` tool to write into `agent_state`; enrich `trace_attributes` with state fields.

### Phase 4: CloudWatch + SSE Complete
Add `emit_agent_state_flush()` to CloudWatch emitter; include state snapshot in `complete` SSE event.

---

## Step by Step Tasks

### 0. Create `server/app/eagle_state.py`

New file — the single source of truth for state schema, mutations, and read projections. **Every other step imports from here; nothing else defines state field names.**

```python
"""
eagle_state.py — EAGLE Unified Agent State Module

Single source of truth for the supervisor agent_state schema.

To add a new state field:
  1. Add it to _DEFAULTS with a safe default value
  2. Optionally handle it in apply_event() if it's mutation-driven
  3. Optionally project it in to_trace_attrs() / to_cw_payload()

That's it. normalize() guarantees the field exists everywhere automatically.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger("eagle.state")

# ── Schema version ────────────────────────────────────────────────────
SCHEMA_VERSION = "1.0"

# ── Canonical defaults ────────────────────────────────────────────────
# THIS IS THE ONLY PLACE THAT DEFINES THE STATE SCHEMA.
# Add new fields here. normalize() fills them in everywhere automatically.
_DEFAULTS: dict = {
    "schema_version": SCHEMA_VERSION,
    "phase": "intake",             # intake | analysis | drafting | review | complete
    "previous_phase": None,
    "package_id": None,            # PKG-YYYY-NNNN
    "required_documents": [],      # ["sow", "igce", "market_research", ...]
    "completed_documents": [],     # subset of required that are done
    "document_versions": {},       # {doc_type: {document_id, version, s3_key}}
    "compliance_alerts": [],       # [{severity, items: [{name, note}]}]
    "turn_count": 0,
    "last_updated": None,          # ISO-8601
    "session_id": None,
}


# ── normalize ─────────────────────────────────────────────────────────

def normalize(state: dict | None) -> dict:
    """Return a state dict with all expected keys present.

    - Missing keys are filled from _DEFAULTS (forward/backward compat)
    - Unknown keys are preserved (additive schema changes are safe)
    - Never mutates the input dict
    """
    out = dict(_DEFAULTS)
    if state:
        out.update(state)
    return out


# ── apply_event ───────────────────────────────────────────────────────

def apply_event(state: dict, state_type: str, params: dict) -> dict:
    """Apply a single update_state event to state. Pure — never mutates input.

    Returns a new normalized state dict with the event applied.
    Single source of truth for how each state_type changes state.
    """
    s = normalize(dict(state))

    if state_type == "phase_change":
        s["previous_phase"] = s["phase"]
        s["phase"] = params.get("phase", s["phase"])
        s["package_id"] = params.get("package_id") or s["package_id"]

    elif state_type == "document_ready":
        doc_type = params.get("doc_type")
        if doc_type and doc_type not in s["completed_documents"]:
            s["completed_documents"] = s["completed_documents"] + [doc_type]
        if doc_type:
            s["document_versions"] = {
                **s["document_versions"],
                doc_type: {
                    "document_id": params.get("document_id"),
                    "version": params.get("version"),
                    "s3_key": params.get("s3_key"),
                },
            }
        s["package_id"] = params.get("package_id") or s["package_id"]

    elif state_type == "checklist_update":
        cl = params.get("checklist", {})
        if cl:
            s["required_documents"] = cl.get("required", s["required_documents"])
            s["completed_documents"] = cl.get("completed", s["completed_documents"])
        s["package_id"] = params.get("package_id") or s["package_id"]

    elif state_type == "compliance_alert":
        s["compliance_alerts"] = s["compliance_alerts"] + [{
            "severity": params.get("severity"),
            "items": params.get("items", []),
        }]

    else:
        logger.warning("eagle_state.apply_event: unknown state_type=%r", state_type)

    return s


# ── Read projections ──────────────────────────────────────────────────

def to_trace_attrs(
    state: dict,
    *,
    tenant_id: str,
    user_id: str,
    tier: str,
    session_id: str,
) -> dict:
    """Build trace_attributes dict for Langfuse/OTEL Agent() constructor.

    Add new Langfuse span attributes here — nowhere else.
    """
    s = normalize(state)
    return {
        "eagle.tenant_id": tenant_id,
        "eagle.user_id": user_id,
        "eagle.tier": tier,
        "eagle.session_id": session_id or "",
        "eagle.phase": s["phase"],
        "eagle.package_id": s["package_id"] or "",
        "eagle.docs_required": len(s["required_documents"]),
        "eagle.docs_completed": len(s["completed_documents"]),
        "eagle.turn_count": s["turn_count"],
    }


def to_cw_payload(state: dict) -> dict:
    """Build CloudWatch data payload for agent.state_flush events.

    Add new CloudWatch fields here — nowhere else.
    """
    s = normalize(state)
    return {
        "schema_version": s["schema_version"],
        "phase": s["phase"],
        "previous_phase": s["previous_phase"],
        "package_id": s["package_id"],
        "docs_required": len(s["required_documents"]),
        "docs_completed": len(s["completed_documents"]),
        "completed_documents": s["completed_documents"],
        "compliance_alert_count": len(s["compliance_alerts"]),
        "turn_count": s["turn_count"],
    }


# ── Stamp ─────────────────────────────────────────────────────────────

def stamp(state: dict) -> dict:
    """Return state with last_updated set to now (UTC ISO-8601). Pure."""
    s = normalize(dict(state))
    s["last_updated"] = datetime.now(timezone.utc).isoformat()
    return s
```

### 1. Update `strands_agentic_service.py` to remove inline state definitions

- Delete the `_default_agent_state()` function (moved to `eagle_state._DEFAULTS`)
- Replace all inline `trace_attributes` dict construction with `to_trace_attrs()`
- Replace all inline state field reads with `normalize()` + projection functions
- Import: `from app.eagle_state import normalize, apply_event, to_trace_attrs, to_cw_payload, stamp`

### 2. Add `load_agent_state` + `save_agent_state` to `session_store.py`

Add after the existing `get_messages` function (around line 416):

```python
# ── Agent State (STATE# records) ─────────────────────────────────────

def load_agent_state(
    session_id: str,
    tenant_id: str = "default",
    user_id: str = "anonymous",
) -> dict | None:
    """Load the latest persisted agent state for a session.

    Returns the state dict if found, None if no state has been saved yet.
    PK: SESSION#{tenant_id}#{user_id}
    SK: STATE#{session_id}
    """
    try:
        table = _get_table()
        response = table.get_item(
            Key={
                "PK": f"SESSION#{tenant_id}#{user_id}",
                "SK": f"STATE#{session_id}",
            }
        )
        item = response.get("Item")
        if not item:
            return None
        content = item.get("content", "{}")
        return json.loads(content) if isinstance(content, str) else content
    except Exception as exc:
        logger.warning("Failed to load agent state for %s: %s", session_id, exc)
        return None


def save_agent_state(
    session_id: str,
    state: dict,
    tenant_id: str = "default",
    user_id: str = "anonymous",
) -> None:
    """Persist agent state for a session (upsert).

    Uses a single STATE# item per session — overwritten on every turn.
    """
    try:
        now = datetime.utcnow().isoformat()
        ttl = int(time.time()) + SESSION_TTL_DAYS * 86400
        table = _get_table()
        table.put_item(Item={
            "PK": f"SESSION#{tenant_id}#{user_id}",
            "SK": f"STATE#{session_id}",
            "session_id": session_id,
            "content": json.dumps(state, default=str),
            "updated_at": now,
            "ttl": ttl,
        })
    except Exception as exc:
        logger.warning("Failed to save agent state for %s: %s", session_id, exc)
```

### 3. Add `AfterInvocationEvent` to `EagleSSEHookProvider`

In `strands_agentic_service.py`, update `EagleSSEHookProvider`:

- Add `tenant_id`, `user_id`, `session_id` params to `__init__`
- Import `AfterInvocationEvent` from `strands.hooks.events`
- Register the new callback in `register_hooks`
- Implement `_on_after_invocation`:

```python
# Add to imports at top
from strands.hooks.events import AfterToolCallEvent, AfterInvocationEvent

class EagleSSEHookProvider(HookProvider):
    def __init__(
        self,
        result_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        tenant_id: str = "default",
        user_id: str = "anonymous",
        session_id: str | None = None,
    ):
        self.result_queue = result_queue
        self.loop = loop
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.session_id = session_id
        self._turn_tool_calls: list[str] = []

    def register_hooks(self, registry):
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(AfterInvocationEvent, self._on_after_invocation)

    # ... existing _on_after_tool_call unchanged ...

    def _on_after_invocation(self, event: AfterInvocationEvent):
        """Flush agent state to DynamoDB after every supervisor turn."""
        if not self.session_id:
            return
        try:
            # event.agent.state is the live dict on the Agent instance
            state = getattr(getattr(event, "agent", None), "state", None)
            if not state or not isinstance(state, dict):
                return

            # Increment turn count
            state["turn_count"] = state.get("turn_count", 0) + 1
            state["last_updated"] = __import__("datetime").datetime.utcnow().isoformat()

            from app.stores.session_store import save_agent_state
            save_agent_state(
                session_id=self.session_id,
                state=state,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
            )
            logger.debug(
                "eagle.state_flushed session=%s phase=%s docs=%d/%d turn=%d",
                self.session_id,
                state.get("phase"),
                len(state.get("completed_documents", [])),
                len(state.get("required_documents", [])),
                state.get("turn_count"),
            )
        except Exception as exc:
            logger.warning("State flush failed (non-fatal): %s", exc)
```

### 4. Update `sdk_query` to load state and pass `agent_state=`

In `sdk_query` (around line 2037), before the `Agent()` constructor call:

```python
from app.stores.session_store import load_agent_state
from app.eagle_state import normalize, to_trace_attrs, stamp

_leaf_session = session_id.split("#")[-1] if session_id and "#" in session_id else session_id
_loaded_state = normalize(
    load_agent_state(_leaf_session, tenant_id, user_id) if _leaf_session else None
)
_loaded_state["session_id"] = _leaf_session

supervisor = Agent(
    model=_model,
    system_prompt=system_prompt,
    tools=skill_tools + service_tools,
    callback_handler=None,
    messages=strands_history,
    agent_state=_loaded_state,
    trace_attributes=to_trace_attrs(
        _loaded_state,
        tenant_id=tenant_id, user_id=user_id, tier=tier, session_id=session_id or "",
    ),
)
```

After `result = supervisor(prompt)`, add state save for the non-streaming path:

```python
try:
    from app.stores.session_store import save_agent_state
    from app.eagle_state import stamp
    final_state = stamp(getattr(result, "state", None) or _loaded_state)
    final_state["turn_count"] = final_state.get("turn_count", 0) + 1
    if _leaf_session:
        save_agent_state(_leaf_session, final_state, tenant_id, user_id)
except Exception as _e:
    logger.warning("State flush (sdk_query) failed: %s", _e)
```

### 5. Update `sdk_query_streaming` to load state and pass `agent_state=`

Same pattern as Step 4, using `eagle_state` helpers throughout:

```python
from app.stores.session_store import load_agent_state
from app.eagle_state import normalize, to_trace_attrs

_leaf_session = session_id.split("#")[-1] if session_id and "#" in session_id else session_id
_loaded_state = normalize(
    load_agent_state(_leaf_session, tenant_id, user_id) if _leaf_session else None
)
_loaded_state["session_id"] = _leaf_session

sse_hook = EagleSSEHookProvider(
    result_queue=result_queue,
    loop=loop,
    tenant_id=tenant_id,
    user_id=user_id,
    session_id=_leaf_session,
)

supervisor = Agent(
    model=_model,
    system_prompt=system_prompt,
    tools=skill_tools + service_tools,
    callback_handler=None,
    messages=strands_history,
    hooks=[sse_hook],
    agent_state=_loaded_state,
    trace_attributes=to_trace_attrs(
        _loaded_state,
        tenant_id=tenant_id, user_id=user_id, tier=tier, session_id=session_id or "",
    ),
)
```

### 6. Update `update_state` tool to write into `agent_state` via `apply_event`

In `strands_agentic_service.py`, find the `update_state` tool factory (around line 1384). After building the SSE metadata payload, call `apply_event()` and merge the result back into `invocation_state`:

```python
from app.eagle_state import apply_event

# After building the SSE metadata payload:
new_state = apply_event(tool_context.invocation_state, state_type, params)
tool_context.invocation_state.update(new_state)
```

That's it — `apply_event` is pure and handles all state_type cases. `invocation_state.update()` merges the new values into Strands' live state dict, which is then available on `result.state` and `event.agent.state` in `AfterInvocationEvent`.

> **Note**: No scattered `if state_type == ...` blocks here anymore — that logic lives exclusively in `eagle_state.apply_event()`.

### 7. Add `emit_agent_state_flush` to `cloudwatch_emitter.py`

Append after the existing `emit_feedback_submitted` function:

```python
def emit_agent_state_flush(
    tenant_id: str,
    session_id: str,
    user_id: str,
    state: dict,
) -> None:
    """Emit a structured agent.state_flush event after every supervisor turn.

    Queryable via CloudWatch Insights:
      fields @timestamp, data.phase, data.docs_completed, data.docs_required
      | filter event_type = "agent.state_flush"
      | stats count() by data.phase
    """
    emit_telemetry_event(
        event_type="agent.state_flush",
        tenant_id=tenant_id,
        session_id=session_id,
        user_id=user_id,
        data={
            "phase": state.get("phase", "intake"),
            "previous_phase": state.get("previous_phase"),
            "package_id": state.get("package_id"),
            "docs_required": len(state.get("required_documents", [])),
            "docs_completed": len(state.get("completed_documents", [])),
            "completed_documents": state.get("completed_documents", []),
            "compliance_alert_count": len(state.get("compliance_alerts", [])),
            "turn_count": state.get("turn_count", 0),
        },
    )
```

The `emit_agent_state_flush` function calls `to_cw_payload(state)` internally — no field names leak into the emitter. Call it from `EagleSSEHookProvider._on_after_invocation` after `save_agent_state`:

```python
try:
    from app.telemetry.cloudwatch_emitter import emit_agent_state_flush
    emit_agent_state_flush(
        tenant_id=self.tenant_id,
        session_id=self.session_id,
        user_id=self.user_id,
        state=state,
    )
except Exception as exc:
    logger.debug("CloudWatch state flush failed (non-fatal): %s", exc)
```

### 8. Include state snapshot in `complete` SSE event

In `sdk_query_streaming`, update **all four** `complete` yield sites to include `agent_state`:

```python
# At the main completion point (around line 2498):
yield {
    "type": "complete",
    "text": final_text,
    "tools_called": tools_called,
    "usage": usage,
    "agent_state": agent_result.state if agent_result and hasattr(agent_result, "state") else {},
}
```

For the fast-path yields (trivial greeting, intake form, fast-path doc), pass the loaded state:

```python
yield {
    "type": "complete",
    "text": trivial["text"],
    "tools_called": [],
    "usage": trivial["usage"],
    "agent_state": _loaded_state,   # rehydrated state, unmodified for fast paths
}
```

The frontend `use-agent-stream.ts` already handles the `complete` event — the `agent_state` field is additive and ignored if not present, so no frontend breaking changes.

### 9. Validate with ruff + pytest

```bash
cd server
ruff check app/strands_agentic_service.py app/stores/session_store.py
python -m pytest tests/test_strands_eval.py -v -k "state" --no-header 2>&1 | head -60
```

---

## Testing Strategy

- **Unit (`eagle_state`)**: Test `normalize()` fills missing keys from defaults; test `apply_event()` for all 4 state_types as pure functions; test `to_trace_attrs()` and `to_cw_payload()` return expected shapes. These tests require zero mocking — pure Python dicts in, dicts out.
- **Unit (integration)**: Mock `load_agent_state` / `save_agent_state` in `test_strands_eval.py` — verify state dict is passed to `Agent()` and returned state is saved
- **Integration**: Run eval test 15 (multi-skill chain) and assert `STATE#` item exists in DynamoDB after the run
- **Langfuse**: After a live run, check Langfuse trace for `eagle.phase`, `eagle.docs_completed`, `eagle.package_id` span attributes

---

## Acceptance Criteria

1. `load_agent_state` / `save_agent_state` exist in `session_store.py` and use `STATE#` SK pattern
2. `sdk_query` and `sdk_query_streaming` both pass `agent_state=_loaded_state` to supervisor `Agent()`
3. After a turn that calls `update_state(state_type="phase_change", ...)`, the next request rehydrates with the updated phase
4. `EagleSSEHookProvider.__init__` accepts `tenant_id`, `user_id`, `session_id` — no existing call sites broken (defaults provided)
5. Langfuse traces contain `eagle.phase` and `eagle.docs_completed` span attributes
6. `_load_state_snapshot()` in `document_agent.py` returns state content (writer now implemented)
7. CloudWatch receives `agent.state_flush` events with `phase`, `docs_completed`, `turn_count` fields
8. `complete` SSE event includes `agent_state` dict on every streaming response
9. Adding a new field to `_DEFAULTS` in `eagle_state.py` is the only required change to propagate it everywhere
10. `ruff check` passes with zero errors
11. Existing eval tests still pass

---

## Validation Commands

```bash
# Level 1 — lint (include new module)
cd server && ruff check app/eagle_state.py app/strands_agentic_service.py app/stores/session_store.py app/telemetry/cloudwatch_emitter.py

# Level 2 — pure unit tests for eagle_state (no mocks needed)
cd server && python -c "
from app.eagle_state import normalize, apply_event, to_trace_attrs, to_cw_payload, stamp

# normalize fills defaults
s = normalize(None)
assert s['phase'] == 'intake', 'default phase'
assert s['turn_count'] == 0, 'default turn_count'

# apply_event is pure
s2 = apply_event(s, 'phase_change', {'phase': 'drafting', 'package_id': 'PKG-001'})
assert s2['phase'] == 'drafting'
assert s2['previous_phase'] == 'intake'
assert s['phase'] == 'intake', 'original unmutated'

# document_ready accumulates
s3 = apply_event(s2, 'document_ready', {'doc_type': 'sow', 'version': 1})
assert 'sow' in s3['completed_documents']

# projections include expected keys
ta = to_trace_attrs(s3, tenant_id='t', user_id='u', tier='advanced', session_id='sess')
assert 'eagle.phase' in ta and 'eagle.docs_completed' in ta

cw = to_cw_payload(s3)
assert 'phase' in cw and 'schema_version' in cw

print('eagle_state: all assertions passed')
"

# Level 2 — unit tests (state-related)
cd server && python -m pytest tests/ -v -k "state or agent_state or session" --no-header

# Level 2 — full eval suite
cd server && python -m pytest tests/test_strands_eval.py -v --no-header 2>&1 | tail -20

# Smoke — verify STATE# written to DynamoDB after a run (requires AWS creds)
python -c "
import boto3, json
t = boto3.resource('dynamodb', region_name='us-east-1').Table('eagle')
resp = t.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues={':pk': 'SESSION#demo-tenant#demo-user', ':sk': 'STATE#'}
)
print(json.dumps([i['SK'] for i in resp['Items']], indent=2))
"

# Smoke — verify agent.state_flush events in CloudWatch (requires AWS creds)
python -c "
import boto3, json
logs = boto3.client('logs', region_name='us-east-1')
resp = logs.filter_log_events(
    logGroupName='/eagle/app',
    filterPattern='{ \$.event_type = \"agent.state_flush\" }',
    limit=5,
)
for e in resp.get('events', []):
    print(json.dumps(json.loads(e['message']), indent=2))
"

# Smoke — verify complete SSE event carries agent_state (local dev)
# Start server, run a chat turn, check the complete event includes agent_state key
```

---

## Notes

- **Langfuse already wired**: `main.py:_setup_langfuse()` calls `StrandsTelemetry.setup_otlp_exporter()` at startup. No new setup needed — just enrich `trace_attributes`.
- **`strands-agents[otel]` and `langfuse` already in `requirements.txt`**: No dependency changes.
- **`invocation_state` → `agent.state` merge**: Strands merges top-level keys written to `invocation_state` in tools back into `agent.state`. Only JSON-serializable values work — no dataclasses or custom objects.
- **Parallel subagents**: Since all `update_state` calls happen on the supervisor's `invocation_state` (subagents return results to the supervisor which then calls `update_state`), the supervisor hook correctly sees the merged final state after all subagents complete.
- **`sdk_query` (non-streaming)**: Uses `AfterInvocationEvent` via hook in streaming path; for non-streaming, state is saved inline after `result = supervisor(prompt)` (Step 4 above).
- **DynamoDB cost**: Single `put_item` per turn — negligible (~$0.000001).
- **`_default_agent_state()` location**: Defined at module level in `strands_agentic_service.py` so it's accessible from both `sdk_query` and `sdk_query_streaming`.

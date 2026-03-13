# Plan: Hook-Driven Document Gating with Contract Requirements Matrix

## Task Description

Wire the contract requirements matrix (deterministic FAR-grounded scoring engine) into Strands SDK `BeforeToolCallEvent` hooks to validate `create_document` and `generate_document` calls before they execute. The hook checks the active package's acquisition context (method, type, value, flags) against the matrix to determine whether the requested document is required, optional, or invalid — then blocks, warns, or enriches accordingly. Leverage the new unified agent state (`eagle_state.py`) from the worktree to track compliance alerts and document progress across turns, and emit structured events to both SSE (frontend) and CloudWatch/Langfuse (observability).

## Objective

When complete:
1. Every `create_document` / `generate_document` call is validated against the contract requirements matrix **before execution**
2. Invalid document requests are blocked with a FAR-grounded explanation (e.g., "Source Selection Plan requires method=negotiated and value>$350K — current package is SAP/$200K")
3. Compliance warnings are surfaced as SSE METADATA events to the frontend in real-time
4. Langfuse traces include compliance validation spans with pass/fail/warn outcomes
5. The unified agent state accumulates compliance alerts and completed documents across turns

## Problem Statement

Today the supervisor can generate any document type regardless of whether it's appropriate for the acquisition scenario. A CO could ask for a Source Selection Plan on a micro-purchase, or a J&A on a competitive acquisition — the agent would happily generate it. The contract requirements matrix already knows the rules (ported from `contract-requirements-matrix.html`), but it's only used as a query tool, not as a gate.

The worktree (`agent-ab09d661`) introduces `eagle_state.py` — a unified agent state module with `normalize()`, `apply_event()`, `to_trace_attrs()`, `to_cw_payload()`, and DynamoDB persistence via `save_agent_state()` / `load_agent_state()`. The `EagleSSEHookProvider` in the worktree already registers `AfterInvocationEvent` for state flush. This plan adds `BeforeToolCallEvent` to the same provider for pre-execution validation.

## Solution Approach

**Single hook provider, two events:**

```
EagleSSEHookProvider
  ├── BeforeToolCallEvent  →  validate_document_request()  →  cancel/warn/pass
  ├── AfterToolCallEvent   →  emit SSE tool_result + metadata (existing)
  └── AfterInvocationEvent →  flush state to DynamoDB + CloudWatch (worktree)
```

**Validation flow:**
1. `BeforeToolCallEvent` fires for every tool call
2. If tool is `create_document` or `generate_document`, extract `doc_type` from params
3. Load acquisition context from agent state (package_id → package_store → method, type, value, flags)
4. Call `contract_matrix.get_requirements()` with the acquisition context
5. Check if `doc_type` is in `required_documents` (pass), `optional_documents` (warn), or neither (block)
6. For blocks: `event.cancel_tool = "..."` with FAR citation
7. For warnings: append to `agent_state.compliance_alerts` + emit SSE METADATA
8. For pass: enrich `invocation_state` with compliance context so AfterToolCallEvent can emit it

## Relevant Files

### Existing Files to Modify

- **`server/app/strands_agentic_service.py`** — Add `BeforeToolCallEvent` to `EagleSSEHookProvider.register_hooks()`. The worktree version already has the class restructured with `AfterInvocationEvent`; this plan adds the before-tool hook.
- **`server/app/eagle_state.py`** (worktree) — Add `"validation_results"` to `_DEFAULTS` schema. Add `apply_event()` handler for `"document_validation"` state_type.
- **`server/app/stream_protocol.py`** — No changes needed (already has METADATA event type for compliance_alert).
- **`server/app/telemetry/cloudwatch_emitter.py`** (worktree) — Add `emit_document_validation()` for CloudWatch Insights queries.

### New Files

- **`server/app/hooks/document_gate.py`** — Pure validation logic extracted from the hook callback. Takes `(doc_type, acquisition_context)` → returns `{action: "pass"|"warn"|"block", reason: str, far_citation: str}`. No side effects — testable independently.
- **`server/tests/test_document_gate.py`** — Unit tests for the validation logic (no Bedrock calls needed).

### Reference Files (read-only)

- `server/app/tools/contract_matrix.py` — `get_requirements()` returns `required_documents` and `optional_documents` with FAR notes
- `server/app/compliance_matrix.py` — `get_requirements()` (older version), `search_far()`
- `server/app/stores/package_store.py` — `get_package()` returns `acquisition_pathway`, `estimated_value`, `required_documents`
- `server/app/package_context_service.py` — `resolve_context()` → `PackageContext` with `acquisition_pathway`, `required_documents`
- `docs/contract-requirements-matrix.html` — Original HTML source (authoritative reference for gating rules)

## Implementation Phases

### Phase 1: Foundation — Validation Logic Module

Extract deterministic validation into a standalone module (`hooks/document_gate.py`) with no dependencies on Strands, hooks, or SSE. This makes it testable and reusable.

### Phase 2: Core — BeforeToolCallEvent Hook

Wire the validation module into `EagleSSEHookProvider` via `BeforeToolCallEvent`. Merge with the worktree's `AfterInvocationEvent` hook so the provider handles all three events.

### Phase 3: Integration — State, SSE, Langfuse

Connect validation results to:
- Agent state (`eagle_state.apply_event("document_validation", ...)`)
- SSE METADATA events (compliance_alert with severity + FAR citation)
- Langfuse trace attributes (validation outcome as span attribute)
- CloudWatch (`emit_document_validation()`)

## Step by Step Tasks

### 1. Merge Worktree Changes into Main Working Tree

The worktree (`agent-ab09d661`) has uncommitted changes to 3 files + 1 new file that this plan depends on. These must land first.

- Copy `server/app/eagle_state.py` from worktree to main
- Apply `session_store.py` diff (adds `load_agent_state()` / `save_agent_state()`)
- Apply `cloudwatch_emitter.py` diff (adds `emit_agent_state_flush()`)
- Apply `strands_agentic_service.py` diff (restructured `EagleSSEHookProvider`, state loading in `sdk_query()` and `sdk_query_streaming()`, `update_state_tool` writes to `agent.state`)
- Run `ruff check app/` to verify clean lint
- Run `python -m pytest tests/ -v --ignore=tests/test_strands_eval.py --ignore=tests/test_strands_service.py` to verify nothing breaks

### 2. Create Document Gating Module (`server/app/hooks/document_gate.py`)

Pure validation logic, no Strands dependencies.

- Create `server/app/hooks/__init__.py` (empty)
- Create `server/app/hooks/document_gate.py` with:

```python
"""Document gating logic — validates doc_type against acquisition context.

Pure functions, no side effects. Called by EagleSSEHookProvider.BeforeToolCallEvent.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationResult:
    action: str          # "pass" | "warn" | "block"
    doc_type: str
    reason: str
    far_citation: str = ""
    required_docs: list[str] = None
    optional_docs: list[str] = None

# Map doc_type aliases to canonical names used by contract_matrix
_DOC_TYPE_CANONICAL = {
    "sow": "SOW / PWS",
    "igce": "IGCE",
    "market_research": "Market Research Report",
    "acquisition_plan": "Acquisition Plan",
    "justification": "J&A / Justification",
    "eval_criteria": "Source Selection Plan",
    "security_checklist": "IT Security & Privacy Certification",
    "section_508": "Section 508 ICT Evaluation",
    "cor_certification": "QASP",
    "contract_type_justification": "D&F (Determination & Findings)",
}

def validate_document_request(
    doc_type: str,
    acquisition_method: str,
    contract_type: str,
    dollar_value: int,
    is_it: bool = False,
    is_services: bool = True,
    is_small_business: bool = False,
    is_rd: bool = False,
) -> ValidationResult:
    """Validate whether doc_type is appropriate for the acquisition context.

    Uses contract_matrix.get_requirements() to get the authoritative doc list,
    then checks if the requested doc_type is required, optional, or invalid.
    """
    from ..tools.contract_matrix import get_requirements

    reqs = get_requirements(
        dollar_value=dollar_value,
        method=acquisition_method,
        contract_type=contract_type,
        is_it=is_it,
        is_services=is_services,
        is_small_business=is_small_business,
        is_rd=is_rd,
    )

    required_names = [d["name"] for d in reqs["required_documents"]]
    optional_names = [d["name"] for d in reqs["optional_documents"]]
    canonical = _DOC_TYPE_CANONICAL.get(doc_type, doc_type)

    # Check required docs
    for doc in reqs["required_documents"]:
        if canonical.lower() in doc["name"].lower() or doc_type in doc["name"].lower():
            return ValidationResult(
                action="pass",
                doc_type=doc_type,
                reason=f"{doc['name']} is required for this acquisition",
                far_citation=doc.get("note", ""),
                required_docs=required_names,
                optional_docs=optional_names,
            )

    # Check optional docs
    for doc in reqs["optional_documents"]:
        if canonical.lower() in doc["name"].lower() or doc_type in doc["name"].lower():
            return ValidationResult(
                action="warn",
                doc_type=doc_type,
                reason=f"{doc['name']} is optional for this acquisition scenario: {doc.get('note', '')}",
                far_citation=doc.get("note", ""),
                required_docs=required_names,
                optional_docs=optional_names,
            )

    # Not found in either list — block
    method_label = acquisition_method.upper().replace("-", " ")
    return ValidationResult(
        action="block",
        doc_type=doc_type,
        reason=(
            f"{canonical} is not required or applicable for "
            f"method={method_label}, type={contract_type.upper()}, "
            f"value=${dollar_value:,}. "
            f"Required documents: {', '.join(required_names)}."
        ),
        far_citation="See FAR Part 4.803 for contract file requirements",
        required_docs=required_names,
        optional_docs=optional_names,
    )

    # Also check matrix errors (e.g., micro-purchase > $15K)
    # These are hard blocks from the matrix itself
    if reqs.get("errors"):
        return ValidationResult(
            action="block",
            doc_type=doc_type,
            reason="; ".join(reqs["errors"]),
            far_citation="",
        )
```

### 3. Add BeforeToolCallEvent to EagleSSEHookProvider

In the worktree's restructured `EagleSSEHookProvider`:

- Import `BeforeToolCallEvent` from `strands.hooks.events`
- Add `registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)` in `register_hooks()`
- Implement `_on_before_tool_call()`:

```python
def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
    """Validate create_document/generate_document calls against contract matrix."""
    tool_name = event.tool_use.get("name", "")
    if tool_name not in ("create_document", "generate_document"):
        return

    # Extract doc_type from tool params
    try:
        params = event.tool_use.get("input", {})
        if isinstance(params, str):
            params = json.loads(params)
        doc_type = params.get("doc_type", "")
    except (json.JSONDecodeError, TypeError, AttributeError):
        return  # Can't parse — let it through

    if not doc_type:
        return  # No doc_type specified — let the tool handle the error

    # Get acquisition context from agent state
    agent_state = getattr(getattr(event, "agent", None), "state", None)
    if not agent_state or not isinstance(agent_state, dict):
        return  # No state — can't validate, let it through

    package_id = agent_state.get("package_id")
    if not package_id:
        return  # Not in package mode — skip validation

    # Load package for acquisition details
    try:
        from .stores.package_store import get_package
        pkg = get_package(self.tenant_id, package_id)
        if not pkg:
            return
    except Exception:
        return  # Package load failed — let it through

    # Map package fields to matrix inputs
    pathway = pkg.get("acquisition_pathway", "simplified")
    _PATHWAY_TO_METHOD = {
        "micro_purchase": "micro",
        "simplified": "sap",
        "full_competition": "negotiated",
        "sole_source": "sole",
    }
    method = _PATHWAY_TO_METHOD.get(pathway, "sap")
    value = int(pkg.get("estimated_value", 0))

    from .hooks.document_gate import validate_document_request
    result = validate_document_request(
        doc_type=doc_type,
        acquisition_method=method,
        contract_type=pkg.get("contract_type", "ffp"),
        dollar_value=value,
        is_it=pkg.get("is_it", False),
        is_services=pkg.get("is_services", True),
        is_small_business=pkg.get("is_small_business", False),
    )

    if result.action == "block":
        event.cancel_tool = (
            f"BLOCKED: {result.reason}\n"
            f"FAR Reference: {result.far_citation}\n"
            f"Required documents for this acquisition: {', '.join(result.required_docs or [])}"
        )
        # Record in agent state
        try:
            from .eagle_state import apply_event
            state = agent_state
            apply_event(state, "compliance_alert", {
                "severity": "critical",
                "items": [{"name": f"Blocked: {doc_type}", "note": result.reason}],
            })
        except Exception:
            pass

    elif result.action == "warn":
        # Don't block — but record the warning in agent state
        try:
            from .eagle_state import apply_event
            state = agent_state
            apply_event(state, "compliance_alert", {
                "severity": "warning",
                "items": [{"name": f"Optional: {doc_type}", "note": result.reason}],
            })
        except Exception:
            pass
```

### 4. Extend eagle_state.py Schema for Validation Results

- Add `"validation_results": []` to `_DEFAULTS`
- Add `"document_validation"` handler in `apply_event()`:

```python
elif state_type == "document_validation":
    s["validation_results"] = s.get("validation_results", []) + [{
        "doc_type": params.get("doc_type"),
        "action": params.get("action"),
        "reason": params.get("reason"),
        "far_citation": params.get("far_citation"),
    }]
```

- Add `"validation_count"` and `"blocked_count"` to `to_cw_payload()`

### 5. Add CloudWatch Emitter for Document Validation

In `server/app/telemetry/cloudwatch_emitter.py`:

```python
def emit_document_validation(
    tenant_id: str,
    session_id: str,
    user_id: str,
    doc_type: str,
    action: str,
    reason: str,
) -> None:
    """Emit agent.document_validation event for CloudWatch Insights.

    Query: fields @timestamp, data.doc_type, data.action, data.reason
           | filter event_type = "agent.document_validation"
           | stats count() by data.action
    """
    emit_telemetry_event(
        event_type="agent.document_validation",
        tenant_id=tenant_id,
        session_id=session_id,
        user_id=user_id,
        data={"doc_type": doc_type, "action": action, "reason": reason},
    )
```

### 6. Write Unit Tests (`server/tests/test_document_gate.py`)

Test the pure validation logic without Bedrock:

- `test_required_doc_passes` — SOW for SAP/$200K → action="pass"
- `test_optional_doc_warns` — Acquisition Plan for SAP/$200K → action="warn"
- `test_invalid_doc_blocks` — Source Selection Plan for micro/$5K → action="block"
- `test_micro_purchase_only_ffp` — Any doc for micro → validates correctly
- `test_cr_type_requires_df` — D&F for CPFF → action="pass"
- `test_sole_source_requires_ja` — J&A for sole source → action="pass"
- `test_it_requires_508` — Section 508 for IT acquisition → action="pass"
- `test_high_value_requires_ap` — Acquisition Plan for $500K negotiated → action="pass"
- `test_block_includes_required_docs_list` — Block response lists what IS required
- `test_missing_context_returns_none` — Graceful handling of missing package data

### 7. Validate

- `ruff check app/ app/hooks/` — zero errors
- `python -m pytest tests/test_document_gate.py -v` — all pass
- `python -m pytest tests/ -v --ignore=tests/test_strands_eval.py --ignore=tests/test_strands_service.py` — no regressions
- `python tests/test_strands_eval.py --tests 15` — supervisor chain still works with hook (doesn't block non-package-mode calls)

## Testing Strategy

**Unit tests (test_document_gate.py):**
- 10+ scenarios covering required/optional/blocked for each acquisition pathway
- No Bedrock calls — pure Python logic
- Tests the `_DOC_TYPE_CANONICAL` mapping covers all 10 doc types
- Tests that block messages include FAR citations

**Integration test (manual or eval):**
- Run eval test 15 (supervisor multi-skill chain) — verify the hook doesn't interfere when there's no package context
- Start server with `LANGFUSE_PUBLIC_KEY` set, send a chat requesting a Source Selection Plan on a micro-purchase package — verify:
  - Tool call is cancelled
  - SSE METADATA compliance_alert is emitted
  - Langfuse trace shows the blocked tool call
  - CloudWatch has `agent.document_validation` event with `action=block`

## Acceptance Criteria

1. `BeforeToolCallEvent` hook fires on `create_document` / `generate_document` tool calls
2. Requests for invalid documents are blocked with a FAR-grounded explanation
3. Requests for optional documents proceed with a warning recorded in agent state
4. When no package context exists (workspace mode), all documents pass (no gating)
5. Compliance alerts appear as SSE METADATA events in the frontend
6. CloudWatch `agent.document_validation` events are queryable
7. Langfuse traces show validation outcomes
8. No regressions in existing tests
9. The worktree's unified agent state (`eagle_state.py`) is the single source of truth for state schema

## Validation Commands

```bash
# Lint
ruff check app/ app/hooks/

# Unit tests — document gate
python -m pytest tests/test_document_gate.py -v

# Regression — existing tests
python -m pytest tests/ -v --ignore=tests/test_strands_eval.py --ignore=tests/test_strands_service.py

# Eval — verify hook doesn't break supervisor chain
EAGLE_BEDROCK_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0 python tests/test_strands_eval.py --tests 9,15

# Syntax check new files
python -c "import py_compile; py_compile.compile('app/hooks/document_gate.py', doraise=True)"
python -c "import py_compile; py_compile.compile('app/eagle_state.py', doraise=True)"
```

## Notes

### Worktree Dependency

This plan depends on the worktree (`agent-ab09d661`) changes landing first. The worktree introduces:
- `eagle_state.py` — unified state schema with `normalize()`, `apply_event()`, `to_trace_attrs()`, `stamp()`
- `session_store.py` — `load_agent_state()` / `save_agent_state()` (DynamoDB STATE# records)
- `cloudwatch_emitter.py` — `emit_agent_state_flush()`
- `strands_agentic_service.py` — restructured `EagleSSEHookProvider` with `AfterInvocationEvent`, state loading/flushing in both `sdk_query()` and `sdk_query_streaming()`, `update_state_tool` writes to `agent.state`

### _DOC_TYPE_CANONICAL Mapping

The mapping between internal doc_type IDs (used by `create_document`) and the names returned by `contract_matrix.get_requirements()` needs careful alignment. The HTML matrix uses names like "SOW / PWS", "IGCE", "Market Research Report" while our tool uses `sow`, `igce`, `market_research`. The mapping in Step 2 handles this, but should be validated against both `contract_matrix.py` and `compliance_matrix.py`.

### Graceful Degradation

The hook must never crash the agent loop. Every external call (package_store, contract_matrix, eagle_state) is wrapped in try/except. If validation fails for any reason, the document request proceeds normally — we fail open, not closed.

### Future: Human-in-the-Loop Interrupts

Strands `BeforeToolCallEvent` supports `event.interrupt(name, reason)` for human-in-the-loop approval. A future enhancement could use this for high-value documents (>$50M acquisitions) or documents requiring HCA approval, where the CO must explicitly confirm before generation proceeds.

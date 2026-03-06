# Canonical Package and Document Flow Plan

Branch target: `feature/canonical-package-document-flow`
Primary scope: backend data model, tool orchestration, API contracts, and migration to a single source of truth for package artifacts.

## 1. Executive Summary

The current system has two document paths:

1. Chat tool path (`create_document`) writes timestamped files directly to S3.
2. Package API path (`/api/packages/.../documents`) writes versioned `DOCUMENT#` records to DynamoDB.

This split causes inconsistency in versioning, checklist completeness, and traceability.

This plan defines one canonical flow:

1. Package-scoped documents are always created through a package document service.
2. DynamoDB stores document metadata and application version history.
3. S3 stores document content at deterministic package/version keys.
4. Chat tool generation can still be used, but it must route into the same package document service when in package mode.

## 2. Goals and Non-Goals

### Goals

1. Single authoritative lifecycle for package artifacts.
2. Deterministic and queryable version history.
3. Clear linkage among tenant, user, session, project, package, and document versions.
4. Backward-compatible transition from existing timestamped S3 documents.
5. Preserve streaming UX while improving storage consistency.

### Non-Goals

1. Rewriting prompt logic or agent behavior semantics.
2. Replacing S3 with DynamoDB blobs.
3. Large redesign of document editor UX in this branch.

## 3. Current State

### 3.1 Chat-Driven Path

1. `/api/invoke` proxies to FastAPI `/api/chat/stream`.
2. Streaming route stores user/assistant messages in `SESSION#...` / `MSG#...`.
3. Tool `create_document` currently writes S3 objects at:
   `eagle/{tenant_id}/{user_id}/documents/{doc_type}_{timestamp}.{ext}`
4. Tool result returns `s3_key`, title, preview content.
5. Frontend stores package-like linkage in browser localStorage.

### 3.2 Package API Path

1. `PACKAGE#` entities in DynamoDB hold package lifecycle and checklist.
2. `DOCUMENT#` entities hold content, `version`, `status`, metadata.
3. New versions supersede prior versions.
4. No canonical linkage to S3 object content today in this path.

### 3.3 Problems

1. Same user action can bypass package versioning.
2. Checklist completeness can diverge from generated docs.
3. History is split across localStorage, S3 filenames, and DynamoDB.
4. No stable API-level artifact identity from chat generation.

## 4. Target Architecture

## 4.1 Canonical Principle

For package mode:

1. All generated artifacts must create a `DOCUMENT#` version record.
2. Every `DOCUMENT#` version must map to exactly one immutable S3 key.
3. Package checklist updates must be derived from `DOCUMENT#` state, not client localStorage.

For non-package mode:

1. Generated docs can be stored as workspace documents (out of package scope).
2. They must not mutate package checklist/status.

## 4.2 Storage Model

### DynamoDB (existing `eagle` single table)

Keep `PACKAGE#` and `DOCUMENT#` model, extend document item shape:

1. `project_id` (optional initially, required after Projects rollout).
2. `session_id` (source chat/session).
3. `s3_bucket`
4. `s3_key`
5. `content_hash` (sha256 of canonical content payload)
6. `change_source` (`agent_tool`, `user_edit`, `import`, `migration`)
7. `parent_version` (explicit predecessor, optional for v1)
8. `created_by_user_id`

Document key pattern remains:

1. `PK = DOCUMENT#{tenant_id}`
2. `SK = DOCUMENT#{package_id}#{doc_type}#{version}`

### S3

Canonical package key format:

`eagle/{tenant_id}/packages/{package_id}/{doc_type}/v{version}/{artifact}.{ext}`

Rules:

1. New app version always creates a new S3 key.
2. Bucket versioning remains enabled as infrastructure safety.
3. App-level version number remains source of truth for user/business logic.

## 5. API Changes

## 5.1 New/Updated Backend Contracts

### A. Package Context Resolution

1. Add `active_package_id` support in chat request context (session metadata + explicit override).
2. Add helper endpoint:
   - `POST /api/packages/resolve-context`
   - Input: `session_id`, optional `package_id`, optional `action`
   - Output: resolved package mode + package context

### B. Document Creation in Package Mode

1. New internal service method: `create_package_document_version(...)`
2. Update tool handler `create_document`:
   - If package mode is active, call canonical package document service.
   - If package mode not active, call workspace document storage path.

### C. Package Document Endpoints

Extend `/api/packages/{package_id}/documents` response fields:

1. `document_id`
2. `version`
3. `status`
4. `s3_key`
5. `change_source`
6. `session_id`
7. `created_at`, `created_by_user_id`

Add:

1. `GET /api/packages/{package_id}/documents/{doc_type}/history`
2. `GET /api/packages/{package_id}/documents/{doc_type}/versions/{version}/download-url`
3. `POST /api/packages/{package_id}/documents/{doc_type}/versions/{version}/promote-final`

### D. Workspace (Non-Package) Documents

Optional but recommended:

1. Introduce `WORKDOC#` entity family for non-package docs, or use metadata table with explicit type.
2. Keep APIs separate from package docs to avoid accidental checklist mutations.

## 5.2 SSE Tool Result Payload Changes

For package-mode `create_document`, return:

1. `mode: "package"`
2. `package_id`
3. `document_id`
4. `doc_type`
5. `version`
6. `s3_key`
7. `status`
8. `title`
9. `word_count`
10. `generated_at`

For non-package mode:

1. `mode: "workspace"`
2. workspace-specific identifiers

## 6. Server Refactor Plan

## 6.1 New Service Modules

1. `app/document_service.py`
   - orchestrates version calculation, S3 write, DDB write, supersession.
2. `app/package_context_service.py`
   - resolves active package by session metadata and request hints.

## 6.2 Existing Module Changes

1. `agentic_service.py`
   - replace direct S3-only save in `_exec_create_document` for package mode.
2. `strands_agentic_service.py`
   - pass package context into service tool execution.
3. `document_store.py`
   - store/retrieve new metadata fields.
4. `package_store.py`
   - add `active_document_map` or derive from latest `DOCUMENT#` query.
5. `main.py`
   - add new history/download endpoints.

## 7. Migration Strategy

## 7.1 Data Backfill Script

Create script:

`scripts/migrate-chat-s3-docs-to-package-records.py`

Steps:

1. Discover candidate S3 keys under legacy path `eagle/{tenant}/{user}/documents/`.
2. Infer doc_type and timestamp from filename.
3. Map to package:
   - if session has explicit package metadata, use it;
   - else optionally keep as workspace docs.
4. Create `DOCUMENT#` versions in chronological order.
5. Write migration audit records (`AUDIT#`).

## 7.2 Dual-Write Window

Temporary phase:

1. Package mode writes canonical records.
2. Legacy fields in tool result retained for frontend compatibility.
3. Feature flag:
   - `CANONICAL_PACKAGE_DOC_FLOW=true`

## 7.3 Cutover

1. Remove any direct package artifact reliance on localStorage.
2. Enforce package mode requirement for package checklist mutations.

## 8. Testing Plan

## 8.1 Unit Tests

1. `document_service` version increment and supersession behavior.
2. S3 key deterministic format and immutability.
3. package-mode vs workspace-mode routing.

## 8.2 Integration Tests

1. Chat `/acquisition-package` -> `create_document` -> `DOCUMENT# v1`.
2. Regeneration -> `v2` + `v1 superseded`.
3. Checklist updates reflect latest document status.
4. Download URL for exact version.

## 8.3 E2E Tests

1. Start package, create SOW, regenerate SOW, verify version chip increases.
2. Submit package blocked if required docs missing.
3. Submit succeeds when required docs complete.

## 9. Observability

Add telemetry fields on document events:

1. `tenant_id`, `user_id`, `session_id`
2. `project_id`, `package_id`
3. `document_id`, `doc_type`, `version`
4. `mode` (`package` or `workspace`)
5. `change_source`

## 10. Rollout Phases

1. Phase 1: Service + schema extension + feature flag off.
2. Phase 2: Route package-mode chat doc generation through new service.
3. Phase 3: Frontend reads canonical version metadata.
4. Phase 4: Backfill old data.
5. Phase 5: Remove legacy assumptions and tighten validation.

## 11. Acceptance Criteria

1. Every package document from chat or API is queryable as `DOCUMENT#` with version.
2. Each document version resolves to one S3 key and downloadable artifact.
3. Package checklist status is correct without localStorage dependency.
4. Regeneration always creates incremented version for same `package_id + doc_type`.
5. No regressions in streaming experience and document cards.

## 12. Risks and Mitigations

1. Risk: incorrect package auto-association.
   Mitigation: explicit confirmation when package context is ambiguous.
2. Risk: migration misclassification.
   Mitigation: dry-run mode + audit report + manual review sample.
3. Risk: frontend expecting legacy tool shape.
   Mitigation: compatibility fields retained for one release window.

## 13. Suggested Task Breakdown (Ticket-Ready)

1. Add package context resolver service + tests.
2. Implement `document_service` canonical write path + tests.
3. Wire `create_document` tool to canonical service for package mode.
4. Extend `DOCUMENT#` schema fields and API serializers.
5. Add history/download/finalize endpoints with authorization checks.
6. Update frontend document card model for `version` + `package_id`.
7. Add migration script and runbook.
8. Add integration and E2E test coverage.
9. Enable feature flag in staging; compare metrics and correctness.
10. Enable in prod; deprecate legacy-only package document flow.


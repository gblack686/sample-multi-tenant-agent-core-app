"""Create Strands migration stories in Jira from docs/jira-new-items-20260302.md.

Creates: 1 epic, 2 Done stories, 7 new stories, 2 label updates.
Uses find_issue_by_summary() for dedup — safe to re-run.
"""
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent dir so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from jira_connect import (
    create_issue,
    find_issue_by_summary,
    add_comment,
    get_headers,
    JIRA_BASE_URL,
)

DRY_RUN = "--dry-run" in sys.argv
PROJECT = "EAGLE"


def update_labels(issue_key: str, add: list[str], remove: list[str]) -> bool:
    """Update labels on an existing issue (add/remove)."""
    url = f"{JIRA_BASE_URL}/rest/api/2/issue/{issue_key}"
    payload = {"update": {"labels": []}}
    for label in add:
        payload["update"]["labels"].append({"add": label})
    for label in remove:
        payload["update"]["labels"].append({"remove": label})
    resp = requests.put(url, headers=get_headers(), json=payload)
    return resp.status_code in (200, 204)


# --- Epic ---
epic = {
    "summary": "Strands Agents SDK Migration & Stabilization",
    "type": "Epic",
    "description": (
        "Migrate EAGLE from Claude Agent SDK to Strands Agents SDK. "
        "Covers core migration (complete), session persistence, health check cleanup, "
        "S3 tool env fix, EC2 runner validation, and AgentCore evaluation."
    ),
    "labels": ["strands-sdk", "assignee:greg"],
}

# --- Done stories ---
done_stories = [
    {
        "summary": "Full migration from Claude Agent SDK to Strands Agents SDK — plan, build, wire, cleanup",
        "labels": ["strands-sdk", "backend", "assignee:greg"],
        "description": (
            "Executed the full 5-phase migration plan to replace Claude Agent SDK with Strands Agents SDK.\n\n"
            "Phase 1: created Strands expert system and validated 3 Bedrock models via POC "
            "(Nova Pro 5/5, Llama 4 4/5, DeepSeek R1 5/5).\n"
            "Phase 2: built strands_agentic_service.py (490 lines) as drop-in replacement with identical API "
            "(sdk_query, sdk_query_single_skill, build_skill_tools, build_supervisor_prompt).\n"
            "Phase 3: wired into streaming_routes.py and main.py — callers unchanged.\n"
            "Phase 5: removed claude-agent-sdk from requirements, archived old tests, updated CLAUDE.md.\n\n"
            "PR: https://github.com/CBIIT/sm_eagle/pull/5 (feat/strands-migration)\n"
            "Commits: 48395e9, ea8d316, ae222ee\n"
            "Plan: .claude/specs/20260302-183000-plan-strands-full-migration-v1.md\n"
            "Architecture Report: docs/development/20260302-140000-report-claude-sdk-vs-strands-v1.md"
        ),
    },
    {
        "summary": "Port eval suite to Strands, fix tool tracking bug, run full 28-test validation — 26/28 pass",
        "labels": ["strands-sdk", "eval", "assignee:greg"],
        "description": (
            "Ported all 28 tests from test_eagle_sdk_eval.py to test_strands_eval.py (2858 lines). "
            "Replaced TraceCollector with StrandsResultCollector. Discovered Strands AgentResult.messages "
            "is empty — tool call history lives in result.metrics.tool_metrics (EventLoopMetrics) using "
            "Bedrock camelCase toolUse format (not Anthropic tool_use). Fixed eval collector and production "
            "strands_agentic_service.sdk_query().\n\n"
            "Full suite result on Nova Pro v1: 26/28 pass. 2 failures are pre-existing S3 bucket env config "
            "(tests 16, 19 — not Strands-related). All skill validations 5/5, supervisor multi-skill chain 5/5, "
            "all 7 UC workflows pass. CloudWatch telemetry: 29 events emitted, 81 metrics published.\n\n"
            "PR: https://github.com/CBIIT/sm_eagle/pull/5 (feat/strands-migration)\n"
            "Commits: ae222ee, 8d91f87\n"
            "Plan: .claude/specs/20260302-183000-plan-strands-full-migration-v1.md — Phase 4"
        ),
    },
]

# --- New stories ---
new_stories = [
    {
        "summary": "Implement session persistence for Strands agents using custom DynamoDB SessionManager",
        "labels": ["strands-sdk", "backend", "assignee:greg"],
        "description": (
            "Currently Strands agents are stateless (fresh Agent() per request). Implement a custom "
            "DynamoDBSessionManager that stores conversation history in the existing eagle DynamoDB table "
            "using the SESSION# prefix pattern. Wire it into sdk_query() so multi-turn conversations resume "
            "context. Must preserve multi-tenant isolation (tenant_id in PK).\n\n"
            "Acceptance Criteria:\n"
            "- Custom SessionManager class implements Strands SessionManager interface\n"
            "- Conversation history stored in DynamoDB SESSION#{tenant}-{user}-{session_id}\n"
            "- sdk_query() accepts session_id and loads prior context\n"
            "- Eval test 2 (session resume) upgraded from simulated to real persistence\n"
            "- Multi-tenant isolation verified (tenant A cannot read tenant B sessions)"
        ),
    },
    {
        "summary": "Fix S3 bucket env var for document tools — eval tests 16 & 19 failing",
        "labels": ["backend", "eval", "assignee:greg"],
        "description": (
            "Eval tests 16 (S3 Document Operations) and 19 (Document Generation) fail because S3_BUCKET "
            "environment variable is empty when running tests locally. The execute_tool() handler reads "
            "os.environ.get('S3_BUCKET', '') which returns empty string. Need to either (a) add S3_BUCKET "
            "to test env setup, or (b) have execute_tool fall back to the documented bucket name from config.\n\n"
            "Acceptance Criteria:\n"
            "- S3_BUCKET resolved from config or env in test context\n"
            "- Eval tests 16 and 19 pass (28/28 green)\n"
            "- No hardcoded bucket names — use config-driven resolution"
        ),
    },
    {
        "summary": "Move MODEL and EAGLE_TOOLS exports from legacy agentic_service.py to strands_agentic_service.py",
        "labels": ["backend", "strands-sdk", "assignee:greg"],
        "description": (
            "streaming_routes.py and main.py still import MODEL and EAGLE_TOOLS from the legacy "
            "agentic_service.py for the health check endpoint. This prevents full removal of the old file. "
            "Move these exports to strands_agentic_service.py or a shared config.py, then update imports. "
            "The execute_tool() function also lives in agentic_service.py — evaluate whether to extract it "
            "to a standalone module.\n\n"
            "Acceptance Criteria:\n"
            "- Health check endpoint imports from strands module or shared config\n"
            "- agentic_service.py can be fully archived (no active imports)\n"
            "- execute_tool() moved to standalone module or kept in clearly-labeled utility file\n"
            "- All 28 eval tests still pass"
        ),
    },
    {
        "summary": "Run full 28-test Strands eval suite on EC2 runner (eagle-runner-dev) and publish results",
        "labels": ["eval", "deployment", "assignee:greg"],
        "description": (
            "The eval suite has been validated locally (26/28 pass). Need to deploy the latest code to the "
            "EC2 runner via git bundle, install strands-agents, and run the full suite. Validate that "
            "CloudWatch telemetry flows correctly from EC2 and that results match local. The EC2 runner uses "
            "IAM instance role (not SSO) so credential handling differs.\n\n"
            "Acceptance Criteria:\n"
            "- Code deployed to EC2 via git bundle\n"
            "- strands-agents pip installed on EC2 (Python 3.12)\n"
            "- Full 28-test suite runs to completion\n"
            "- CloudWatch telemetry emitted from EC2 matches local format\n"
            "- Results archived to S3"
        ),
    },
    {
        "summary": "Replace sync Agent() call with stream_async() for real-time SSE token streaming",
        "labels": ["strands-sdk", "backend", "frontend", "assignee:greg"],
        "description": (
            "Currently sdk_query() makes a synchronous supervisor(prompt) call and yields the full response "
            "as a single AssistantMessage. This means the frontend gets the entire response at once (no "
            "token-by-token streaming). Implement Strands stream_async() with a custom CallbackHandler that "
            "emits SSE events as tokens arrive. This will restore the real-time typing effect the frontend "
            "had with the Claude SDK streaming path.\n\n"
            "Acceptance Criteria:\n"
            "- sdk_query() uses agent.stream_async() instead of agent(prompt)\n"
            "- Custom CallbackHandler converts token events to SSE via MultiAgentStreamWriter\n"
            "- Frontend receives incremental text updates (visible typing effect)\n"
            "- Tool use events streamed in real-time (not batched at end)\n"
            "- Error handling preserves current behavior (ERROR SSE event on failure)"
        ),
    },
    {
        "summary": "Evaluate Amazon Bedrock AgentCore as managed runtime for EAGLE agent deployment",
        "labels": ["aws", "strands-sdk", "deployment", "assignee:greg"],
        "description": (
            "AgentCore provides serverless agent runtime with per-session microVMs, I/O-aware billing, "
            "built-in session management, and auto-scaling. Evaluate whether AgentCore adds value over "
            "current ECS Fargate deployment. Key questions: (1) Do NCI IAM SCP constraints allow AgentCore "
            "roles? (2) Does I/O-aware billing reduce costs vs always-on Fargate? (3) Can built-in session "
            "management replace our custom DynamoDB SessionManager? (4) Does code interpreter sandbox "
            "benefit our document generation use case?\n\n"
            "Acceptance Criteria:\n"
            "- AgentCore spike tested in NCI sandbox account\n"
            "- IAM/SCP compatibility verified\n"
            "- Cost comparison: AgentCore vs ECS Fargate for EAGLE workload\n"
            "- Go/no-go decision documented"
        ),
    },
    {
        "summary": "Validate frontend chat interface works end-to-end with Strands streaming backend",
        "labels": ["frontend", "backend", "assignee:fullstack"],
        "description": (
            "With the backend now running Strands instead of Claude SDK, verify the full SSE streaming "
            "pipeline works: frontend sends POST /api/chat/stream → streaming_routes.py → sdk_query() → "
            "Strands Agent → adapter messages → SSE events → frontend renders. Test with the chat interface "
            "on localhost. Verify agent selection, tool use indicators, and cost ticker all render correctly.\n\n"
            "Acceptance Criteria:\n"
            "- Chat messages flow through Strands backend and render in frontend\n"
            "- Tool use events display in agent trace panel\n"
            "- Multi-agent delegation visible (supervisor → specialist)\n"
            "- Error states handled gracefully (SSE ERROR event → UI notification)\n"
            "- Playwright smoke test passes"
        ),
    },
]

# --- Label updates ---
label_updates = [
    {"key": "EAGLE-32", "add": ["strands-sdk"], "remove": ["claude-sdk"],
     "note": "Routing now via @tool-wrapped subagents in strands_agentic_service.py"},
    {"key": "EAGLE-36", "add": ["strands-sdk"], "remove": ["claude-sdk"],
     "note": "Session persistence is a Strands follow-up (EAGLE-42)"},
]


def main():
    mode = "DRY-RUN" if DRY_RUN else "LIVE"
    print(f"=== Create Strands Stories — {mode} ===\n")

    created = []
    skipped = []
    failed = []

    # 1. Epic
    print("--- Epic ---")
    existing = find_issue_by_summary(PROJECT, epic["summary"])
    if existing:
        print(f"  [SKIP] {existing} — {epic['summary']}")
        skipped.append(existing)
    elif DRY_RUN:
        print(f"  [WOULD CREATE] Epic: {epic['summary']}")
    else:
        key = create_issue(PROJECT, epic["summary"], "Epic", epic["description"])
        if key:
            # Add labels
            update_labels(key, epic["labels"], [])
            print(f"  [CREATED] {key} — {epic['summary']}")
            created.append(key)
        else:
            print(f"  [FAIL] Epic: {epic['summary']}")
            failed.append(epic["summary"])

    # 2. Done stories
    print("\n--- Done Stories ---")
    for story in done_stories:
        existing = find_issue_by_summary(PROJECT, story["summary"])
        if existing:
            print(f"  [SKIP] {existing} — {story['summary'][:70]}...")
            skipped.append(existing)
        elif DRY_RUN:
            print(f"  [WOULD CREATE] Story (Done): {story['summary'][:70]}...")
        else:
            key = create_issue(PROJECT, story["summary"], "Story", story["description"])
            if key:
                update_labels(key, story["labels"], [])
                print(f"  [CREATED] {key} — {story['summary'][:70]}...")
                created.append(key)
            else:
                print(f"  [FAIL] {story['summary'][:70]}...")
                failed.append(story["summary"])

    # 3. New stories
    print("\n--- New Stories ---")
    for story in new_stories:
        existing = find_issue_by_summary(PROJECT, story["summary"])
        if existing:
            print(f"  [SKIP] {existing} — {story['summary'][:70]}...")
            skipped.append(existing)
        elif DRY_RUN:
            print(f"  [WOULD CREATE] Story: {story['summary'][:70]}...")
        else:
            key = create_issue(PROJECT, story["summary"], "Story", story["description"])
            if key:
                update_labels(key, story["labels"], [])
                print(f"  [CREATED] {key} — {story['summary'][:70]}...")
                created.append(key)
            else:
                print(f"  [FAIL] {story['summary'][:70]}...")
                failed.append(story["summary"])

    # 4. Label updates
    print("\n--- Label Updates ---")
    for update in label_updates:
        if DRY_RUN:
            print(f"  [WOULD UPDATE] {update['key']}: +{update['add']} -{update['remove']}")
        else:
            ok = update_labels(update["key"], update["add"], update["remove"])
            if ok:
                print(f"  [UPDATED] {update['key']}: +{update['add']} -{update['remove']}")
                # Add note as comment
                add_comment(update["key"], update["note"])
            else:
                print(f"  [FAIL] {update['key']}: label update failed")
                failed.append(update["key"])

    # Summary
    print(f"\n=== Summary ===")
    print(f"Created : {len(created)}")
    print(f"Skipped : {len(skipped)} (already exist)")
    print(f"Failed  : {len(failed)}")
    print(f"Labels  : {len(label_updates)} updates")
    print(f"Mode    : {mode}")

    if created:
        print(f"\nNew issues:")
        for key in created:
            print(f"  {key}")


if __name__ == "__main__":
    main()

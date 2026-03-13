"""Generate EAGLE Strands Agents Architecture Excalidraw diagram."""
import json
import os

elements = []
seed = 1000

# Colors
PURPLE_S, PURPLE_B = "#6d28d9", "#ede9fe"
BLUE_S, BLUE_B = "#1e40af", "#dbeafe"
ORANGE_S, ORANGE_B = "#b45309", "#fef3c7"
GREEN_S, GREEN_B = "#047857", "#d1fae5"
RED_S, RED_B = "#b91c1c", "#fee2e2"
CYAN_S, CYAN_B = "#0e7490", "#cffafe"
GRAY = "#6b7280"
DARK = "#111827"
TITLE_C = "#1e3a5f"


def rect(id, x, y, w, h, stroke, bg, sw=2, bound_ids=None):
    global seed; seed += 1
    be = [{"id": bid, "type": "text"} for bid in (bound_ids or [])]
    elements.append({
        "id": id, "type": "rectangle", "x": x, "y": y,
        "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg,
        "fillStyle": "solid", "strokeWidth": sw, "roughness": 1,
        "opacity": 100, "groupIds": [],
        "roundness": {"type": 3},
        "seed": seed, "version": 1, "versionNonce": seed + 100,
        "isDeleted": False, "boundElements": be or [],
        "updated": 1, "link": None, "locked": False
    })


def text(id, x, y, txt, sz=16, fam=1, color=DARK, align="left", cid=None, va="top", w=None):
    global seed; seed += 1
    lines = txt.split("\n")
    cw = w or max(len(l) * sz * 0.6 for l in lines) + 10
    ch = len(lines) * sz * 1.25
    elements.append({
        "id": id, "type": "text", "x": x, "y": y,
        "width": cw, "height": ch, "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "roughness": 1,
        "opacity": 100, "groupIds": [], "seed": seed,
        "version": 1, "versionNonce": seed + 100,
        "isDeleted": False, "boundElements": None,
        "updated": 1, "link": None, "locked": False,
        "text": txt, "fontSize": sz, "fontFamily": fam,
        "textAlign": align if not cid else "center",
        "verticalAlign": va if not cid else "middle",
        "containerId": cid, "originalText": txt, "lineHeight": 1.25
    })


def arrow(id, x1, y1, x2, y2, color=GRAY, sw=2, sid=None, eid=None):
    global seed; seed += 1
    dx, dy = x2 - x1, y2 - y1
    sb = {"elementId": sid, "focus": 0, "gap": 5} if sid else None
    eb = {"elementId": eid, "focus": 0, "gap": 5} if eid else None
    elements.append({
        "id": id, "type": "arrow", "x": x1, "y": y1,
        "width": abs(dx), "height": abs(dy), "angle": 0,
        "strokeColor": color, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": sw, "roughness": 1,
        "opacity": 100, "groupIds": [],
        "roundness": {"type": 2},
        "seed": seed, "version": 1, "versionNonce": seed + 100,
        "isDeleted": False, "boundElements": None,
        "updated": 1, "link": None, "locked": False,
        "points": [[0, 0], [dx, dy]],
        "lastCommittedPoint": None,
        "startBinding": sb, "endBinding": eb,
        "startArrowhead": None, "endArrowhead": "arrow"
    })


# ═══════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════
text("title", 520, 15, "EAGLE Strands Agents Architecture", 44, 3, TITLE_C, "center", w=1100)
text("subtitle", 420, 65, "Supervisor -> Subagent Orchestration  |  Hooks  |  Unified State  |  Langfuse OTEL", 17, 1, GRAY, "center", w=1300)

# ═══════════════════════════════════════════════════════════════
# DATA FLOW ROW (y: 100-170)
# ═══════════════════════════════════════════════════════════════
rect("user_r", 80, 105, 130, 55, GREEN_S, GREEN_B, 3, ["user_t"])
text("user_t", 95, 118, "User", 22, 3, GREEN_S, cid="user_r", va="middle")

rect("api_r", 300, 100, 230, 65, BLUE_S, BLUE_B, 2, ["api_t"])
text("api_t", 320, 108, "FastAPI\nPOST /api/chat", 17, 1, BLUE_S, cid="api_r")

rect("sdk_r", 620, 100, 310, 65, PURPLE_S, PURPLE_B, 2, ["sdk_t"])
text("sdk_t", 635, 108, "sdk_query_streaming()\nasyncio.Queue -> SSE", 16, 1, PURPLE_S, cid="sdk_r")

rect("lf_r", 1640, 100, 260, 70, PURPLE_S, PURPLE_B, 2, ["lf_t"])
text("lf_t", 1655, 108, "Langfuse Cloud\nOTEL Traces + Spans", 17, 1, PURPLE_S, cid="lf_r")

arrow("a_user_api", 210, 132, 300, 132, DARK, 2, "user_r", "api_r")
arrow("a_api_sdk", 530, 132, 620, 132, DARK, 2, "api_r", "sdk_r")

# ═══════════════════════════════════════════════════════════════
# SUPERVISOR AGENT (center focal, y: 200-690)
# ═══════════════════════════════════════════════════════════════
rect("super_r", 500, 200, 580, 500, PURPLE_S, PURPLE_B, 4)
text("super_title", 520, 210, "Supervisor Agent", 28, 3, PURPLE_S)
text("super_body", 520, 250,
     "BedrockModel (boto3-native Bedrock)\n"
     "us.anthropic.claude-haiku-4-5-20251001-v1:0\n"
     "\n"
     "System Prompt (4-layer resolution):\n"
     "  1. Workspace override (wspc_store)\n"
     "  2. DynamoDB PLUGIN# canonical\n"
     "  3. Bundled eagle-plugin/ files\n"
     "  4. Tenant custom SKILL# items\n"
     "\n"
     "State: eagle_state.normalize()\n"
     "  phase | package_id | turn_count\n"
     "  required_documents | completed_documents\n"
     "  compliance_alerts | validation_results\n"
     "\n"
     "trace_attributes -> Langfuse session.id\n"
     "callback_handler -> MultiAgentStreamWriter\n"
     "hook_provider -> EagleSSEHookProvider\n"
     "\n"
     "Extended Thinking: budget_tokens=8000",
     14, 1, DARK)

arrow("a_sdk_super", 775, 165, 775, 200, PURPLE_S, 2, "sdk_r", "super_r")

# Arrow from supervisor to langfuse
arrow("a_super_lf", 1080, 135, 1640, 135, PURPLE_S, 2, "super_r", "lf_r")

# ═══════════════════════════════════════════════════════════════
# WRITE TOOLS (left, y: 200-440)
# ═══════════════════════════════════════════════════════════════
rect("write_r", 15, 200, 460, 245, ORANGE_S, ORANGE_B)
text("write_title", 30, 208, "Write Tools (Supervisor Only)", 18, 3, ORANGE_S)
text("write_body", 30, 238,
     "create_document     Generate acq docs (10 types)\n"
     "generate_document   AI-driven doc content (doc_agent)\n"
     "s3_document_ops     Read/write/list S3 per-tenant\n"
     "dynamodb_intake     CRUD intake records\n"
     "intake_workflow     Start/advance/complete workflow\n"
     "update_state        Push state changes (eagle_state)\n"
     "manage_skills       CRUD custom skills\n"
     "manage_prompts      Agent prompt overrides\n"
     "manage_templates    Document template overrides\n"
     "get_intake_status   Package completeness check",
     13, 1, DARK)

arrow("a_write_super", 475, 320, 500, 320, ORANGE_S, 2, "write_r", "super_r")

# ═══════════════════════════════════════════════════════════════
# READ TOOLS (left, y: 465-650)
# ═══════════════════════════════════════════════════════════════
rect("read_r", 15, 465, 460, 195, GREEN_S, GREEN_B)
text("read_title", 30, 473, "Read Tools (Shared with Subagents)", 18, 3, GREEN_S)
text("read_body", 30, 503,
     "knowledge_search      DynamoDB KB metadata\n"
     "knowledge_fetch       S3 full doc content\n"
     "search_far            FAR/DFARS clause search\n"
     "query_compliance_matrix  Compliance requirements\n"
     "query_contract_matrix    FAR 16.104 scoring\n"
     "web_search            Web/news/gov search\n"
     "browse_url            Fetch URLs/PDFs\n"
     "code_execute          Sandbox code execution",
     13, 1, DARK)

arrow("a_read_super", 475, 560, 500, 560, GREEN_S, 2, "read_r", "super_r")

# ═══════════════════════════════════════════════════════════════
# PROGRESSIVE DISCLOSURE (left, y: 680-720)
# ═══════════════════════════════════════════════════════════════
rect("prog_r", 15, 680, 460, 45, CYAN_S, CYAN_B)
text("prog_t", 30, 688, "Progressive: list_skills -> load_skill -> load_data", 14, 1, CYAN_S)

# ═══════════════════════════════════════════════════════════════
# 7 SPECIALIST SUBAGENTS (right, y: 200-690)
# ═══════════════════════════════════════════════════════════════
rect("sub_container", 1110, 200, 790, 500, BLUE_S, "#f0f5ff", 3)
text("sub_title", 1130, 208, "7 Specialist Subagents (@tool-wrapped)", 20, 3, BLUE_S)
text("sub_hint", 1130, 236, "All get: knowledge_search + knowledge_fetch + load_data", 13, 1, GRAY)

subagents = [
    ("sa1", "legal-counsel", "FAR/DFARS compliance, clause analysis, J&A review", "+ search_far, query_compliance_matrix"),
    ("sa2", "market-intelligence", "Market research, vendor analysis, pricing data", "+ search_far"),
    ("sa3", "tech-translator", "Technical specs to acquisition language", "+ search_far, query_compliance_matrix"),
    ("sa4", "public-interest", "Public interest determinations, D&F support", "+ search_far"),
    ("sa5", "policy-supervisor", "Policy oversight, regulatory alignment", "+ search_far, query_compliance_matrix"),
    ("sa6", "policy-librarian", "Policy library lookups, precedent research", "+ search_far"),
    ("sa7", "policy-analyst", "Policy analysis, regulatory impact assessment", "+ search_far, query_compliance_matrix"),
]

y_start = 265
for i, (sid, name, desc, tools) in enumerate(subagents):
    y = y_start + i * 60
    rect(f"{sid}_r", 1125, y, 760, 52, BLUE_S, BLUE_B)
    text(f"{sid}_name", 1135, y + 5, name, 16, 3, BLUE_S)
    text(f"{sid}_desc", 1135, y + 26, f"{desc}   [{tools}]", 12, 1, GRAY)

arrow("a_super_sub", 1080, 450, 1110, 450, BLUE_S, 3, "super_r", "sub_container")

# ═══════════════════════════════════════════════════════════════
# HOOK SYSTEM (bottom left, y: 760-1130)
# ═══════════════════════════════════════════════════════════════
rect("hooks_r", 15, 760, 730, 380, RED_S, "#fff5f5", 3)
text("hooks_title", 30, 768, "EagleSSEHookProvider (HookProvider)", 22, 3, RED_S)
text("hooks_sub", 30, 798, "register_hooks(registry) -> 4 Callbacks on Strands Agent lifecycle", 14, 1, GRAY)

# 4 hook event boxes (2x2 grid)
rect("h1_r", 30, 830, 345, 70, RED_S, RED_B)
text("h1_t", 40, 838,
     "BeforeToolCallEvent\n"
     "-> Doc gating (create_document/generate_document)\n"
     "-> CloudWatch emit_tool_started",
     12, 1, DARK)

rect("h2_r", 385, 830, 345, 70, RED_S, RED_B)
text("h2_t", 395, 838,
     "AfterToolCallEvent\n"
     "-> State delta tracking (phase, docs, pkg)\n"
     "-> CloudWatch emit_tool_completed",
     12, 1, DARK)

rect("h3_r", 30, 912, 345, 70, RED_S, RED_B)
text("h3_t", 40, 920,
     "AfterModelCallEvent\n"
     "-> Verify update_state called before end_turn\n"
     "-> CloudWatch warning if skipped",
     12, 1, DARK)

rect("h4_r", 385, 912, 345, 70, RED_S, RED_B)
text("h4_t", 395, 920,
     "AfterInvocationEvent\n"
     "-> DynamoDB state flush (save_agent_state)\n"
     "-> CloudWatch emit_agent_state_flush",
     12, 1, DARK)

# Contract Matrix + Document Gate
rect("matrix_r", 30, 1000, 345, 80, ORANGE_S, ORANGE_B)
text("matrix_t", 40, 1008,
     "Contract Requirements Matrix\n"
     "9 methods | 10 types | 14 thresholds\n"
     "FAR 16.104 scoring (13 factors)\n"
     "tools/contract_matrix.py",
     12, 1, DARK)

rect("gate_r", 385, 1000, 345, 80, RED_S, "#fef2f2")
text("gate_t", 395, 1008,
     "document_gate.py\n"
     "validate_document_request()\n"
     "pass | warn | block\n"
     "16 doc_type canonical mappings",
     12, 1, DARK)

# Arrows within hooks
arrow("a_matrix_gate", 375, 1040, 385, 1040, ORANGE_S, 2, "matrix_r", "gate_r")
arrow("a_gate_h1", 557, 1000, 200, 900, RED_S, 2, "gate_r", "h1_r")

# Arrow from supervisor to hooks
arrow("a_super_hooks", 700, 700, 380, 760, RED_S, 2, "super_r", "hooks_r")

# ═══════════════════════════════════════════════════════════════
# UNIFIED AGENT STATE (bottom center, y: 760-1130)
# ═══════════════════════════════════════════════════════════════
rect("state_r", 775, 760, 580, 380, GREEN_S, "#f0fdf4", 3)
text("state_title", 790, 768, "Unified Agent State (eagle_state.py)", 20, 3, GREEN_S)
text("state_body", 790, 800,
     "Schema v1.0 — Single source of truth\n"
     "\n"
     "phase: intake|analysis|drafting|review|complete\n"
     "package_id: PKG-YYYY-NNNN\n"
     "required_documents: [sow, igce, ...]\n"
     "completed_documents: [subset of required]\n"
     "document_versions: {doc_type: {id, ver, s3_key}}\n"
     "compliance_alerts: [{severity, items}]\n"
     "validation_results: [{doc_type, action, reason}]\n"
     "turn_count: int  |  last_updated: ISO-8601",
     13, 1, DARK)

# 4 output targets
rect("out_ddb", 790, 1000, 130, 55, GREEN_S, GREEN_B, 2, ["out_ddb_t"])
text("out_ddb_t", 800, 1010, "DynamoDB\nsave_state", 13, 1, GREEN_S, cid="out_ddb")

rect("out_cw", 930, 1000, 130, 55, GREEN_S, GREEN_B, 2, ["out_cw_t"])
text("out_cw_t", 940, 1010, "CloudWatch\nto_cw_payload", 13, 1, GREEN_S, cid="out_cw")

rect("out_lf", 1070, 1000, 130, 55, PURPLE_S, PURPLE_B, 2, ["out_lf_t"])
text("out_lf_t", 1080, 1010, "Langfuse\ntrace_attrs", 13, 1, PURPLE_S, cid="out_lf")

rect("out_sse", 1210, 1000, 130, 55, CYAN_S, CYAN_B, 2, ["out_sse_t"])
text("out_sse_t", 1220, 1010, "SSE\nMETADATA", 13, 1, CYAN_S, cid="out_sse")

text("state_fns", 790, 1065,
     "normalize()  apply_event()  to_trace_attrs()  to_cw_payload()  stamp()",
     12, 1, GRAY)

# Arrow from supervisor to state
arrow("a_super_state", 850, 700, 1065, 760, GREEN_S, 2, "super_r", "state_r")

# ═══════════════════════════════════════════════════════════════
# SSE OUTPUT + FRONTEND (bottom right, y: 760-1050)
# ═══════════════════════════════════════════════════════════════
rect("sse_r", 1385, 760, 515, 105, CYAN_S, CYAN_B, 3)
text("sse_title", 1400, 770, "MultiAgentStreamWriter", 18, 3, CYAN_S)
text("sse_body", 1400, 800,
     "SSE Events: text | tool_use | tool_result\n"
     "            complete | error | metadata\n"
     "stream_protocol.py -> asyncio.Queue",
     13, 1, DARK)

rect("fe_r", 1385, 895, 515, 95, BLUE_S, BLUE_B, 3)
text("fe_title", 1400, 905, "Next.js Frontend", 18, 3, BLUE_S)
text("fe_body", 1400, 935,
     "use-agent-stream.ts (SSE consumer hook)\n"
     "simple-chat-interface.tsx\n"
     "Activity panel: tool cards, state updates",
     13, 1, DARK)

arrow("a_sse_fe", 1642, 865, 1642, 895, CYAN_S, 2, "sse_r", "fe_r")

# Arrow from supervisor to SSE
arrow("a_super_sse", 1080, 650, 1385, 810, CYAN_S, 2, "super_r", "sse_r")

# ═══════════════════════════════════════════════════════════════
# LEGEND (bottom right corner)
# ═══════════════════════════════════════════════════════════════
rect("legend_r", 1385, 1020, 515, 120, GRAY, "#fafafa", 1)
text("legend_title", 1400, 1028, "Legend", 16, 3, GRAY)
text("legend_body", 1400, 1052,
     "Purple = Supervisor/Agent core\n"
     "Blue = Subagents / API layer\n"
     "Orange = Write tools / Data mutation\n"
     "Green = Read tools / State management\n"
     "Red = Hooks / Validation / Gating\n"
     "Cyan = SSE streaming / Output",
     12, 1, GRAY)

# ═══════════════════════════════════════════════════════════════
# BUILD FILE
# ═══════════════════════════════════════════════════════════════
excalidraw_json = {
    "type": "excalidraw",
    "version": 2,
    "source": "https://excalidraw.com",
    "elements": elements,
    "appState": {"viewBackgroundColor": "#ffffff"},
    "files": {}
}

# Build text elements section
text_section_lines = []
for el in elements:
    if el["type"] == "text":
        first_line = el["text"].split("\n")[0]
        text_section_lines.append(f"{first_line} ^{el['id']}")

# Build the .excalidraw.md file
output = f"""---
excalidraw-plugin: parsed
tags: [excalidraw]
---

# Text Elements

{chr(10).join(text_section_lines)}

%%
# Drawing
```json
{json.dumps(excalidraw_json, indent=2)}
```
%%
"""

# Save
dest_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "architecture", "diagrams", "excalidraw")
dest_file = os.path.join(dest_dir, "20260312-200000-arch-strands-agents-system-v1.excalidraw.md")
os.makedirs(dest_dir, exist_ok=True)
with open(dest_file, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Generated {len(elements)} elements")
print(f"Saved to: {dest_file}")

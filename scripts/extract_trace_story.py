#!/usr/bin/env python3
"""
Extract a full trace story from Langfuse showing supervisor + subagent reasoning chain.

Strands observation hierarchy:
  AGEN: invoke_agent (supervisor)             ← root
    SPAN: execute_event_loop_cycle            ← one per LLM turn
      GENE: chat                              ← LLM call (input=messages list, output={message: JSON})
      TOOL: <skill_name>                      ← tool call span
        AGEN: invoke_agent (subagent)         ← nested agent
          SPAN: execute_event_loop_cycle
            GENE: chat                        ← subagent LLM call

Usage:
    python scripts/extract_trace_story.py [trace_id] [output_path]
"""
import os, sys, json, base64, urllib.request, urllib.error
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "server" / ".env", override=False)

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
_AUTH = base64.b64encode(
    f"{os.environ['LANGFUSE_PUBLIC_KEY']}:{os.environ['LANGFUSE_SECRET_KEY']}".encode()
).decode()
_HEADERS = {"Authorization": f"Basic {_AUTH}"}


def api_get(path: str) -> dict:
    req = urllib.request.Request(f"{LANGFUSE_HOST}{path}", headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {path}: {e.read().decode()}") from e


def find_latest_trace(session_id: str) -> str:
    data = api_get(f"/api/public/traces?sessionId={session_id}&limit=5")
    traces = sorted(data.get("data", []), key=lambda t: t.get("timestamp", ""), reverse=True)
    if not traces:
        raise ValueError(f"No traces for session {session_id}")
    return traces[0]["id"]


def get_observations(trace_id: str) -> list:
    all_obs, page = [], 1
    while True:
        data = api_get(f"/api/public/observations?traceId={trace_id}&limit=50&page={page}")
        items = data.get("data", [])
        all_obs.extend(items)
        if len(all_obs) >= data.get("meta", {}).get("totalItems", len(items)):
            break
        page += 1
    return all_obs


# ── Block parsing ────────────────────────────────────────────────────────────

def parse_blocks(raw, max_text=4000) -> list:
    """Convert Strands/Bedrock block list into normalized typed dicts."""
    if not raw:
        return []
    items = raw if isinstance(raw, list) else [raw]
    out = []
    for item in items:
        if isinstance(item, str):
            out.append({"type": "text", "text": item[:max_text]})
        elif isinstance(item, dict):
            if "text" in item:
                out.append({"type": "text", "text": str(item["text"])[:max_text]})
            elif "toolUse" in item:
                tu = item["toolUse"]
                out.append({
                    "type": "tool_use",
                    "id": tu.get("toolUseId", ""),
                    "name": tu.get("name", ""),
                    "input": tu.get("input", {}),
                })
            elif "toolResult" in item:
                tr = item["toolResult"]
                content = tr.get("content", [])
                text = ""
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and "text" in c:
                            text += c["text"]
                elif isinstance(content, str):
                    text = content
                out.append({
                    "type": "tool_result",
                    "id": tr.get("toolUseId", ""),
                    "status": tr.get("status", ""),
                    "content": text[:max_text],
                })
            elif "reasoningContent" in item:
                rc = item["reasoningContent"]
                rt = rc.get("reasoningText", {}) if isinstance(rc, dict) else {}
                text = rt.get("text", "") if isinstance(rt, dict) else str(rt)
                out.append({"type": "reasoning", "text": text[:max_text]})
    return out


def parse_gen(obs: dict) -> dict:
    """Parse a GENERATION observation into {prompt_messages, response_blocks, usage}."""
    inp = obs.get("input") or []
    out_raw = obs.get("output") or {}

    # input is a list of {role, content:[blocks]} objects
    messages = []
    if isinstance(inp, list):
        for msg in inp:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, list):
                blocks = parse_blocks(content)
            elif isinstance(content, str):
                blocks = parse_blocks([{"text": content}])
            else:
                blocks = []
            messages.append({"role": role, "blocks": blocks})

    # output is {finish_reason, message} where message is a JSON-encoded block list
    response_blocks = []
    if isinstance(out_raw, dict):
        msg_val = out_raw.get("message", "")
        if isinstance(msg_val, str) and msg_val.strip().startswith("["):
            try:
                response_blocks = parse_blocks(json.loads(msg_val))
            except json.JSONDecodeError:
                response_blocks = [{"type": "text", "text": msg_val[:4000]}]
        elif isinstance(msg_val, list):
            response_blocks = parse_blocks(msg_val)
        elif isinstance(msg_val, str) and msg_val:
            response_blocks = [{"type": "text", "text": msg_val[:4000]}]
    elif isinstance(out_raw, str):
        response_blocks = [{"type": "text", "text": out_raw[:4000]}]

    usage = obs.get("usage") or {}
    return {
        "model": obs.get("model", ""),
        "prompt_messages": messages,
        "response_blocks": response_blocks,
        "usage": {
            "input_tokens": usage.get("promptTokens", usage.get("input", 0)),
            "output_tokens": usage.get("completionTokens", usage.get("output", 0)),
        },
        "latency_ms": round(obs.get("latency", 0) or 0),
    }


# ── Story builder ─────────────────────────────────────────────────────────────

def build_story(trace_id: str) -> dict:
    trace_meta = api_get(f"/api/public/traces/{trace_id}")
    observations = get_observations(trace_id)

    print(f"  Total observations: {len(observations)}")
    obs_by_id = {o["id"]: o for o in observations}

    # Parent → children map
    children: dict[str, list] = {}
    for o in observations:
        pid = o.get("parentObservationId")
        if pid:
            children.setdefault(pid, []).append(o)

    def kids(oid, typ_prefix=None) -> list:
        cs = children.get(oid, [])
        if typ_prefix:
            cs = [c for c in cs if (c.get("type") or "").startswith(typ_prefix)]
        return sorted(cs, key=lambda x: x.get("startTime", ""))

    def direct_gen(oid) -> dict | None:
        """Return the first GENERATION that is a direct child of oid (sorted by startTime)."""
        gens = sorted(
            [c for c in children.get(oid, []) if (c.get("type") or "").startswith("GEN")],
            key=lambda x: x.get("startTime", ""),
        )
        return gens[0] if gens else None

    # Find root supervisor AGEN
    root_agens = [o for o in observations
                  if (o.get("type") or "").startswith("AGEN") and not o.get("parentObservationId")]
    if not root_agens:
        return {"error": "No root AGEN found", "trace_id": trace_id}
    supervisor = root_agens[0]

    # Walk supervisor's execute_event_loop_cycle spans
    cycles = kids(supervisor["id"], "SPAN")
    story_turns = []

    for i, cycle in enumerate(cycles):
        # Get this cycle's LLM generation (direct child only)
        gen_obs = direct_gen(cycle["id"])
        if not gen_obs:
            continue
        gen_data = parse_gen(gen_obs)

        # Get user prompt from first user message
        user_prompt = None
        for msg in gen_data["prompt_messages"]:
            if msg["role"] == "user":
                for blk in msg["blocks"]:
                    if blk["type"] == "text":
                        txt = blk["text"].strip()
                        # Handle case where content is a JSON-encoded list of blocks
                        if txt.startswith("[{"):
                            try:
                                inner = json.loads(txt)
                                for ib in inner:
                                    if isinstance(ib, dict) and "text" in ib:
                                        user_prompt = ib["text"]
                                        break
                            except Exception:
                                user_prompt = txt
                        else:
                            user_prompt = txt
                        break
                break

        turn: dict = {
            "turn": i + 1,
            "agent": "supervisor",
            "user_prompt": user_prompt,
            "response": gen_data["response_blocks"],
            "model": gen_data["model"],
            "usage": gen_data["usage"],
            "latency_ms": gen_data["latency_ms"],
        }

        # Get tool calls in this cycle
        tool_spans = kids(cycle["id"], "TOOL")
        tool_calls = []

        for tool_span in tool_spans:
            tool_name = tool_span["name"]

            # Tool call input from supervisor's response (toolUse block)
            tool_input_query = None
            for blk in gen_data["response_blocks"]:
                if blk["type"] == "tool_use" and blk["name"] == tool_name:
                    tool_input_query = blk.get("input", {})
                    break

            # Subagent AGEN nested under this TOOL span
            sub_agens = kids(tool_span["id"], "AGEN")
            subagent_data = None
            if sub_agens:
                sub_agen = sub_agens[0]
                sub_cycles = kids(sub_agen["id"], "SPAN")
                sub_llm_calls = []
                for sc in sub_cycles:
                    sg = direct_gen(sc["id"])
                    if sg:
                        sg_data = parse_gen(sg)
                        # Subagent user prompt
                        sub_user_prompt = None
                        for msg in sg_data["prompt_messages"]:
                            if msg["role"] == "user":
                                for blk in msg["blocks"]:
                                    if blk["type"] == "text":
                                        txt = blk["text"].strip()
                                        if txt.startswith("[{"):
                                            try:
                                                inner = json.loads(txt)
                                                for ib in inner:
                                                    if isinstance(ib, dict) and "text" in ib:
                                                        sub_user_prompt = ib["text"]
                                                        break
                                            except Exception:
                                                sub_user_prompt = txt
                                        else:
                                            sub_user_prompt = txt
                                        break
                                break
                        sub_llm_calls.append({
                            "user_prompt": sub_user_prompt,
                            "response": sg_data["response_blocks"],
                            "model": sg_data["model"],
                            "usage": sg_data["usage"],
                            "latency_ms": sg_data["latency_ms"],
                        })
                subagent_data = {
                    "name": tool_name,
                    "llm_calls": sub_llm_calls,
                    "has_reasoning": any(
                        any(b["type"] == "reasoning" for b in lc["response"])
                        for lc in sub_llm_calls
                    ),
                }

            tool_calls.append({
                "tool_name": tool_name,
                "input": tool_input_query,
                "subagent": subagent_data,
            })

        if tool_calls:
            turn["tool_calls"] = tool_calls

        story_turns.append(turn)

    return {
        "trace_id": trace_id,
        "session_id": trace_meta.get("sessionId"),
        "timestamp": trace_meta.get("timestamp"),
        "trace_name": trace_meta.get("name"),
        "total_observations": len(observations),
        "supervisor_turns": len(story_turns),
        "story": story_turns,
    }


# ── Pretty printer ────────────────────────────────────────────────────────────

def pprint_story(story: dict):
    sep = "=" * 72
    thin = "─" * 72
    print(f"\n{sep}")
    print("FULL TRACE STORY")
    print(f"Trace:   {story['trace_id']}")
    print(f"Session: {story['session_id']}")
    print(f"Time:    {story['timestamp']}")
    print(f"Turns:   {story['supervisor_turns']}")
    print(sep)

    for turn in story.get("story", []):
        t = turn["turn"]
        print(f"\n{thin}")
        print(f"SUPERVISOR TURN {t}")
        print(thin)

        if t == 1 and turn.get("user_prompt"):
            print(f"\n>>> USER PROMPT")
            print(f"    {turn['user_prompt'][:400]}")

        has_reasoning = any(b["type"] == "reasoning" for b in turn.get("response", []))
        resp_blocks = turn.get("response", [])
        print(f"\n>>> SUPERVISOR RESPONSE  [{len(resp_blocks)} blocks | model={turn.get('model','?')[:30]} | {turn['usage']['input_tokens']}in/{turn['usage']['output_tokens']}out tokens]")
        if has_reasoning:
            print("    *** EXTENDED THINKING ACTIVE ***")
        for blk in resp_blocks:
            btype = blk["type"]
            if btype == "text":
                txt = blk["text"]
                print(f"    [text] {txt[:300]}{'...' if len(txt)>300 else ''}")
            elif btype == "reasoning":
                print(f"    [reasoning] {blk['text'][:200]}...")
            elif btype == "tool_use":
                inp = blk.get("input", {})
                q = inp.get("query", inp.get("prompt", str(inp)))
                print(f"    [→ CALL TOOL] {blk['name']}")
                print(f"    [  query] {str(q)[:300]}")
            elif btype == "tool_result":
                print(f"    [← TOOL RESULT] status={blk['status']} len={len(blk['content'])}")

        # Tool calls + subagents
        for tc in turn.get("tool_calls", []):
            tool = tc["tool_name"]
            sub = tc.get("subagent")
            if not sub:
                continue
            print(f"\n  ┌─── SUBAGENT: {tool.upper()} ───")
            for j, lc in enumerate(sub.get("llm_calls", [])):
                up = lc.get("user_prompt", "")
                print(f"  │  [SUBAGENT PROMPT] {str(up)[:300]}")
                has_r = any(b["type"] == "reasoning" for b in lc.get("response", []))
                resp = lc.get("response", [])
                print(f"  │  [SUBAGENT RESPONSE] [{len(resp)} blocks | {lc['usage']['input_tokens']}in/{lc['usage']['output_tokens']}out tokens]")
                if has_r:
                    print(f"  │  *** REASONING BLOCKS PRESENT ***")
                for blk in resp[:6]:
                    btype = blk["type"]
                    if btype == "text":
                        print(f"  │    [text] {blk['text'][:300]}")
                    elif btype == "reasoning":
                        print(f"  │    [reasoning] {blk['text'][:200]}")
                    elif btype == "tool_use":
                        print(f"  │    [tool_use] {blk['name']}")
                    elif btype == "tool_result":
                        print(f"  │    [tool_result] {blk.get('content','')[:100]}")
            print(f"  └──────────────────────────────")


def main():
    session_id = "nci-oa-premium-co-johnson-001-eval-015"
    if len(sys.argv) >= 2:
        trace_id = sys.argv[1]
    else:
        print(f"Looking up latest trace for session: {session_id}")
        trace_id = find_latest_trace(session_id)
        print(f"Found trace: {trace_id}")

    output_path = sys.argv[2] if len(sys.argv) >= 3 else f"data/eval/results/trace-story-{trace_id[:8]}.json"

    print(f"\nExtracting story from trace {trace_id}...")
    story = build_story(trace_id)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(story, indent=2, default=str))
    print(f"\nSaved to: {output_path}")

    pprint_story(story)


if __name__ == "__main__":
    main()

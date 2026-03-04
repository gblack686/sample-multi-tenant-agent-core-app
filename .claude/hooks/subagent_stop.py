#!/usr/bin/env python3
"""SubagentStop hook — tracks expert agent completions for self-improve scheduling.

TAC Pattern: ACT-LEARN-REUSE feedback loop.
When an expert agent finishes a plan/build task, log it so the orchestrator
knows to run self-improve on that domain's expertise.

Hook event: SubagentStop
Input (stdin JSON): { session_id, agent_id, agent_type, agent_transcript_path, ... }
Output (stdout JSON): { hookSpecificOutput: { additionalContext: "..." } }
"""

import json
import sys
import os
from datetime import datetime

# Expert agent domains — maps agent_type to expert domain name
EXPERT_AGENTS = {
    "frontend-expert-agent": "frontend",
    "backend-expert-agent": "backend",
    "eval-expert-agent": "eval",
    "aws-expert-agent": "aws",
    "claude-sdk-expert-agent": "strands",
    "cloudwatch-expert-agent": "cloudwatch",
    "deployment-expert-agent": "deployment",
    "git-expert-agent": "git",
    "hooks-expert-agent": "hooks",
    "tac-expert-agent": "tac",
}

PENDING_FILE = os.path.join(
    os.path.dirname(__file__), "..", "pending-self-improve.json"
)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    agent_type = data.get("agent_type", "")

    # Only track expert agents
    domain = EXPERT_AGENTS.get(agent_type)
    if not domain:
        sys.exit(0)

    # Append to pending self-improve list
    entry = {
        "domain": domain,
        "agent_type": agent_type,
        "agent_id": data.get("agent_id", ""),
        "timestamp": datetime.now().isoformat(),
    }

    pending = []
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, "r") as f:
                pending = json.load(f)
        except (json.JSONDecodeError, IOError):
            pending = []

    # Deduplicate by domain — keep latest only
    pending = [p for p in pending if p.get("domain") != domain]
    pending.append(entry)

    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2)

    # Inject reminder into context
    result = {
        "hookSpecificOutput": {
            "additionalContext": (
                f"Expert agent '{agent_type}' completed. "
                f"If this was a plan/build task, run "
                f"/experts:{domain}:self-improve to update expertise."
            )
        }
    }
    json.dump(result, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()

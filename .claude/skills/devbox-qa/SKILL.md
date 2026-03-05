# devbox-qa — EC2 Devbox QA via SSM SendCommand

Run the EAGLE QA smoke test suite against the EC2 devbox from inside the VPC.
Uses `ssm:SendCommand` (AWS-RunShellScript) — **not** `ssm:StartSession` — so it
works even when interactive SSM sessions are blocked by `poweruser-deny-policy`.

Tests run directly on the EC2 instance against `http://localhost:3000` (frontend)
and `http://localhost:8000` (backend), so they're inside the VPC and hit the real
docker-compose stack with no port-forwarding needed.

## Invoke

```
/devbox-qa                        # Full smoke test (health + curl + playwright)
/devbox-qa health                 # Health checks only (fast, no browser)
/devbox-qa curl                   # Curl-based API tests only
/devbox-qa playwright             # Playwright browser tests only
/devbox-qa deploy                 # Deploy latest hub/main then run full QA
/devbox-qa email                  # Full QA + video recording + email report
/devbox-qa playwright email       # Playwright only + video + email
/devbox-qa health email           # Health checks + email (no video)
```

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| MODE | `full` | `health` / `curl` / `playwright` / `full` / `deploy` |
| EMAIL | `false` | Set to `true` when `email` keyword present — activates QA Extension |
| INSTANCE_ID | auto (from CF stack `eagle-ec2-dev`) | EC2 instance ID override |
| BRANCH | `main` | Branch to deploy (only used in `deploy` mode) |
| AWS_PROFILE | `eagle` | AWS profile with SSM SendCommand access |
| REPO_DIR | `/home/eagle/eagle` | Path to repo on EC2 |
| COMPOSE_FILE | `deployment/docker-compose.dev.yml` | Docker compose file path |

## Allowed Tools

`Bash`, `Read`

---

## Workflow

### Phase 0: Resolve Instance ID

```bash
# Try CloudFormation stack output first
INSTANCE_ID=$(AWS_PROFILE=eagle aws cloudformation describe-stacks \
  --stack-name eagle-ec2-dev --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" \
  --output text 2>/dev/null)

# Fallback: hardcoded devbox from EAGLE memory
INSTANCE_ID="${INSTANCE_ID:-i-0390c06d166d18926}"
echo "Target: $INSTANCE_ID"
```

### Phase 1: Verify SSM SendCommand Access

Before running tests, confirm `ssm:SendCommand` is allowed (distinct from the
blocked `ssm:StartSession`):

```bash
AWS_PROFILE=eagle aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["echo ssm-ok"]' \
  --region us-east-1 \
  --query "Command.CommandId" --output text
```

If this fails with AccessDeniedException → report that SendCommand is also blocked
and suggest the tunnel fallback (see Phase 6).

Poll for result:
```bash
AWS_PROFILE=eagle aws ssm get-command-invocation \
  --command-id "$CMD_ID" \
  --instance-id "$INSTANCE_ID" \
  --region us-east-1 \
  --query "[Status,StandardOutputContent]" --output text
```

### Phase 2 (deploy mode only): Sync Code

```bash
python scripts/devbox_deploy.py deploy --branch "$BRANCH" --repo origin
```

Wait for success before proceeding to Phase 3.

### Phase 3: Health Checks

Run via `ssm_run` / SendCommand:

```bash
commands = [
  "echo '=== Docker containers ==='",
  f"cd {REPO_DIR} && docker compose -f {COMPOSE_FILE} ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'",
  "echo ''",
  "echo '=== Backend /api/health ==='",
  "curl -sf http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || echo 'FAIL: backend not responding'",
  "echo ''",
  "echo '=== Frontend HTTP status ==='",
  "curl -so /dev/null -w 'Frontend: HTTP %{http_code}\n' http://localhost:3000/ || echo 'FAIL: frontend not responding'",
]
```

Expected:
- Docker: backend + frontend containers `Up`
- Backend: `{"status": "healthy", ...}`
- Frontend: `HTTP 200`

### Phase 4: Curl-Based API Tests

Run via SendCommand — tests core API endpoints from inside the VPC:

```bash
commands = [
  "BASE=http://localhost:8000",
  "FRONT=http://localhost:3000",
  "PASS=0; FAIL=0",
  "",
  "check() { local label=$1 url=$2 expect=$3",
  "  result=$(curl -sf \"$url\" 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); print(d.get('$expect','MISSING'))\" 2>/dev/null)",
  "  if [ \"$result\" != 'MISSING' ] && [ -n \"$result\" ]; then",
  "    echo \"PASS $label ($result)\"; PASS=$((PASS+1))",
  "  else echo \"FAIL $label\"; FAIL=$((FAIL+1)); fi }",
  "",
  "check 'health-status'   \"$BASE/api/health\"    'status'",
  "check 'health-version'  \"$BASE/api/health\"    'version'",
  "check 'health-model'    \"$BASE/api/health\"    'model'",
  "",
  "# Sessions endpoint",
  "STATUS=$(curl -so /dev/null -w '%{http_code}' \"$BASE/api/sessions\" 2>/dev/null)",
  "[ \"$STATUS\" = '200' ] && echo \"PASS sessions-endpoint\" && PASS=$((PASS+1)) || echo \"FAIL sessions-endpoint (HTTP $STATUS)\" && FAIL=$((FAIL+1))",
  "",
  "# Tools endpoint",
  "STATUS=$(curl -so /dev/null -w '%{http_code}' \"$BASE/api/tools\" 2>/dev/null)",
  "[ \"$STATUS\" = '200' ] && echo \"PASS tools-endpoint\" && PASS=$((PASS+1)) || echo \"FAIL tools-endpoint (HTTP $STATUS)\" && FAIL=$((FAIL+1))",
  "",
  "# Frontend serves HTML",
  "CONTENT=$(curl -sf \"$FRONT/\" 2>/dev/null | grep -c '<html' || echo 0)",
  "[ \"$CONTENT\" -ge 1 ] && echo 'PASS frontend-html' && PASS=$((PASS+1)) || echo 'FAIL frontend-html' && FAIL=$((FAIL+1))",
  "",
  "echo ''",
  "echo \"Results: $PASS passed, $FAIL failed\"",
]
```

### Phase 5: Playwright Browser Tests (playwright mode / full mode)

Check if Playwright is installed on EC2, install if needed, then run:

```bash
commands = [
  # Install playwright if missing
  "if ! command -v npx &>/dev/null; then",
  "  echo 'node/npx not found — skipping playwright tests'",
  "  exit 0",
  "fi",
  f"cd {REPO_DIR}/client",
  # Install if node_modules missing
  "[ -d node_modules ] || npm ci --quiet",
  # Install playwright browsers if missing
  "npx playwright install chromium --with-deps 2>/dev/null | tail -5 || true",
  # Run smoke tests against localhost
  "BASE_URL=http://localhost:3000 npx playwright test navigation.spec.ts --project=chromium --reporter=line 2>&1 | tail -30",
]
```

If playwright is not installed, fall back to curl results and note in the report.

### Phase 6: Tunnel Fallback (if SendCommand also blocked)

If both `ssm:StartSession` and `ssm:SendCommand` are blocked:

```
⚠️  Both SSM StartSession and SendCommand are blocked by poweruser-deny-policy.

Options:
1. Request ssm:SendCommand allowance for i-0390c06d166d18926 in poweruser-deny-policy
2. Run QA locally via tunnel once StartSession is unblocked:
     just devbox-tunnel          # Terminal 1 — keep running
     /mcp-browser:eagle-smoke-test http://localhost:3000   # Terminal 2
3. Run QA against the ECS/ALB endpoint directly (if publicly accessible)
```

---

## Report Format

```
# EAGLE Devbox QA Report

**Instance:** i-0390c06d166d18926 (eagle-runner-dev)
**Mode:** {MODE}
**Date:** {ISO timestamp}
**Branch:** {branch on EC2}

## Health Checks
| Service   | Status | Detail |
|-----------|--------|--------|
| Backend   | ✅/❌  | HTTP 200 / {"status":"healthy"} |
| Frontend  | ✅/❌  | HTTP 200 |
| Containers| ✅/❌  | Up X minutes |

## API Tests (N/N passed)
| Test                | Result |
|---------------------|--------|
| health-status       | ✅/❌  |
| health-version      | ✅/❌  |
| sessions-endpoint   | ✅/❌  |
| tools-endpoint      | ✅/❌  |
| frontend-html       | ✅/❌  |

## Playwright Tests
{playwright output or "Skipped — not installed"}

## Issues Found
{only if failures — describe each}

**Overall:** ✅ ALL PASSED / ❌ {N} FAILED
```

---

## Implementation Notes

- Use `devbox_deploy.py`'s `ssm_run()` pattern for all remote commands (polls until complete)
- `ssm:SendCommand` ≠ `ssm:StartSession` — they are separate IAM actions. SendCommand
  is the key that makes this work even when interactive sessions are blocked.
- All tests target `http://localhost:*` from inside the EC2 — no NAT/ALB/public IP needed
- Timeout: health=60s, curl=90s, playwright=300s
- Always run health first; skip playwright if health fails
- If the instance is stopped, start it with `just devbox-start i-0390c06d166d18926`
  and wait ~15s for SSM agent to connect before retrying

---

## QA Extension: Video Recording + Email Report

This extension wraps the standard phases above with a git commit step, video
recording, an AI-generated summary, and an SES email dispatch to
`gregory.black@nih.gov`.

### Invoke

```
/devbox-qa email                  # Full QA + video + email report
/devbox-qa playwright email       # Playwright only + video + email
/devbox-qa health email           # Health checks + email (no video)
```

The `email` keyword activates this extension. All other MODE flags work as before.

---

### QA-Phase 0: Commit to QA Branch (always, before tests)

Generate a timestamped branch name and commit any dirty working tree:

```bash
QA_BRANCH="qa/$(date -u +%Y%m%d-%H%M%S)"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create and switch to QA branch
git checkout -b "$QA_BRANCH"

# Stage and commit only if there are changes
if ! git diff --quiet || ! git diff --cached --quiet; then
  git add -A
  git commit -m "chore: qa snapshot $(date -u +%Y-%m-%dT%H:%M:%SZ) [skip ci]"
  echo "Committed working tree to $QA_BRANCH"
else
  echo "Working tree clean — QA branch created: $QA_BRANCH (no commit needed)"
fi
```

Store `QA_BRANCH` and `QA_RUN_ID` (= the branch suffix, e.g. `20260305-143000`)
for use in later phases. Do NOT push the branch unless MODE=deploy.

---

### QA-Phase 5.5: Enable Video Recording

**For EC2 playwright tests (MODE=playwright or full):**

Patch the SSM playwright command to add `--video=on` and capture output dir:

```bash
# Appended to the Phase 5 playwright SSM commands:
"VIDEO_DIR=/tmp/eagle-qa-videos/$QA_RUN_ID",
"mkdir -p $VIDEO_DIR",
f"cd {REPO_DIR}/client",
f"BASE_URL=http://localhost:3000 npx playwright test navigation.spec.ts \
  --project=chromium --reporter=line \
  --video=on --output=$VIDEO_DIR 2>&1 | tail -50",
```

After playwright finishes, sync the video dir to S3:

```bash
# Run via SSM SendCommand after Phase 5:
commands = [
  f"VIDEO_DIR=/tmp/eagle-qa-videos/{QA_RUN_ID}",
  f"S3_PATH=s3://eagle-eval-artifacts-695681773636-dev/qa-videos/{QA_RUN_ID}/",
  "aws s3 sync $VIDEO_DIR $S3_PATH --region us-east-1 2>&1 | tail -10",
  "echo S3_UPLOAD_DONE",
]
```

**For local MCP browser tests (claude-bowser / playwright-bowser):**

Set the video output env var before invoking the browser skill:

```bash
export PLAYWRIGHT_VIDEO_DIR="./client/screenshots/qa-videos/$QA_RUN_ID"
mkdir -p "$PLAYWRIGHT_VIDEO_DIR"
# Then invoke the browser skill as normal — playwright MCP will record to that dir
```

After the skill completes, upload the local video dir to S3:

```bash
AWS_PROFILE=eagle aws s3 sync "./client/screenshots/qa-videos/$QA_RUN_ID" \
  "s3://eagle-eval-artifacts-695681773636-dev/qa-videos/$QA_RUN_ID/" \
  --region us-east-1
```

Store the S3 path as `VIDEO_S3_PATH` for use in the email phase.

**If no video file is found** after the run (e.g., health-only mode), set
`VIDEO_S3_PATH=""` and skip the video link in the email.

---

### QA-Phase 8: AI Summary Generation

Collect all stdout from Phases 3–5 into a single `RAW_OUTPUT` string.
Then produce a structured summary block:

```
## AI Summary

**Overall:** ✅ ALL PASSED / ❌ {N} FAILED

**Key Findings:**
- {1-sentence result for health checks}
- {1-sentence result for API/curl tests}
- {1-sentence result for playwright tests, or "Skipped"}

**Action Required:** {only if failures — one sentence describing what to fix, or "None"}
```

Rules for generating the summary:
- Be concise — 3–5 bullet points max
- Lead with the overall pass/fail verdict
- Mention any specific failed test by name
- If everything passed, say so in one sentence and add "No action required"
- Do NOT repeat the full table — the full table appears below in the email body

---

### QA-Phase 9: Generate Presigned URL + Publish to SNS

SNS is used instead of SES direct-send because NIH mail gateways reject
AWS SES relay for @nih.gov/@nci.nih.gov addresses. SNS sends from Amazon's
own infrastructure and bypasses this restriction.

**Topic ARN:** `arn:aws:sns:us-east-1:695681773636:eagle-eval-alerts-dev`
**Subscribers:** `gregory.black@nih.gov`, `blackga@nci.nih.gov`
(both confirmed 2026-03-05)

#### Step 1 — Generate presigned URL (if video exists)

```bash
if [ -n "$VIDEO_S3_PATH" ]; then
  VIDEO_KEY=$(AWS_PROFILE=eagle aws s3 ls "$VIDEO_S3_PATH" --region us-east-1 \
    | grep -E '\.(webm|mp4)' | head -1 | awk '{print $NF}')
  BUCKET="eagle-eval-artifacts-695681773636-dev"
  FULL_KEY="qa-videos/$QA_RUN_ID/$VIDEO_KEY"

  PRESIGNED_URL=$(AWS_PROFILE=eagle aws s3 presign \
    "s3://$BUCKET/$FULL_KEY" \
    --expires-in 604800 \
    --region us-east-1)
fi
```

#### Step 2 — Compose SNS message (plain text)

```
SUBJECT = f"EAGLE QA — {QA_RUN_ID} — PASSED / FAILED ({N} issues)"

MESSAGE = f"""
EAGLE QA Report
===============
Run ID:   {QA_RUN_ID}
Branch:   {QA_BRANCH}
Instance: {INSTANCE_ID}
Mode:     {MODE}
Date:     {ISO_TIMESTAMP}

AI SUMMARY
----------
{AI_SUMMARY}

FULL RESULTS
------------
{FULL_REPORT_TABLE}

VIDEO RECORDING
---------------
{PRESIGNED_URL if PRESIGNED_URL else "No video recorded (health-only mode)"}
Link expires in 7 days.
"""
```

#### Step 3 — Publish to SNS

```bash
AWS_PROFILE=eagle aws sns publish \
  --region us-east-1 \
  --topic-arn "arn:aws:sns:us-east-1:695681773636:eagle-eval-alerts-dev" \
  --subject "$SUBJECT" \
  --message "$MESSAGE"
```

On success, print:
```
📧 QA report published to eagle-eval-alerts-dev
   Subscribers: gregory.black@nih.gov, blackga@nci.nih.gov
   Subject: {SUBJECT}
   Video:   {PRESIGNED_URL or "no video"}
   Branch:  {QA_BRANCH}
```

On failure, print the full report to stdout so results are not lost.

---

### Email Extension — Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SNS_TOPIC_ARN | `arn:aws:sns:us-east-1:695681773636:eagle-eval-alerts-dev` | SNS topic for QA reports |
| VIDEO_BUCKET | `eagle-eval-artifacts-695681773636-dev` | S3 bucket for video upload |
| VIDEO_PREFIX | `qa-videos/` | S3 key prefix |
| PRESIGN_EXPIRY | `604800` | Presigned URL TTL in seconds (7 days) |
| QA_BRANCH_PREFIX | `qa/` | Git branch prefix for snapshots |

### Email Extension — Notes

- **Delivery**: SNS sends from Amazon's own mail infrastructure — no SPF
  conflict with NIH mail gateways. Both subscribers confirmed 2026-03-05.
- **Adding subscribers**: `aws sns subscribe --topic-arn ... --protocol email --notification-endpoint <address>`
- Video recording requires Playwright ≥ 1.20. If `--video=on` is unsupported,
  fall back to screenshots-only and omit the video line from the message.
- The QA branch commit uses `[skip ci]` to avoid triggering GitHub Actions
  on a test snapshot. Remove if CI validation on QA snapshots is desired.

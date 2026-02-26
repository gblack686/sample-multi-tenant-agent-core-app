---
name: smoke-test
description: Run Eagle Playwright smoke tests. Use when the user wants to run smoke tests, check if the app is working end-to-end, test the chat, or verify the deployment. Supports two modes: full-stack on the EC2 dev box (all 31 tests), or against the deployed Fargate ALB (28 tests, skips localhost:8000).
---

# Eagle Smoke Test Skill

Run the full Playwright smoke test suite against Eagle. There are two modes:

| Mode | Tests | When to use |
|------|-------|-------------|
| **EC2 full-stack** | 31/31 (incl. localhost:8000) | Verifying a complete stack; default choice |
| **Fargate ALB** | 28/31 (skips backend-direct tests) | Quick check against deployed prod stack |

Every EC2 full-stack run automatically:
1. Records video for every test (`video: 'on'` in playwright.config.ts)
2. Uploads videos/traces/screenshots to `s3://eagle-documents-695681773636-dev/smoke-results/{run_id}/test-results/`
3. Writes a run metadata record to the `eagle` DynamoDB table (`PK=SMOKE_RUN#{run_id}`, `SK=METADATA`)

---

## Mode 1: EC2 Full-Stack (Recommended)

Starts frontend + backend via Docker Compose on `eagle-runner-dev`, then runs all 31 Playwright tests.

### How it works

1. SSM sends a command to EC2 that downloads `run-smoke.sh` from S3 and executes it
2. The script fetches IMDSv2 credentials, writes `.env`, runs `docker compose up --build`, waits for backend, then runs Playwright
3. Results are printed to SSM output

### Run it

```bash
COMMAND_ID=$(aws ssm send-command \
  --instance-ids i-0390c06d166d18926 \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=[
    "aws s3 cp s3://eagle-documents-695681773636-dev/scripts/run-smoke.sh /tmp/run-smoke.sh --region us-east-1",
    "sed -i s/\\r// /tmp/run-smoke.sh",
    "chmod +x /tmp/run-smoke.sh",
    "bash /tmp/run-smoke.sh 2>&1"
  ]' \
  --timeout-seconds 600 \
  --region us-east-1 \
  --query "Command.CommandId" --output text)

echo "Command ID: $COMMAND_ID"
```

### Check results

```bash
# Poll until done (InProgress → Success/Failed)
aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id i-0390c06d166d18926 \
  --region us-east-1 \
  --query "[Status, StatusDetails]"

# Get full output
aws ssm get-command-invocation \
  --command-id "$COMMAND_ID" \
  --instance-id i-0390c06d166d18926 \
  --region us-east-1 \
  --query "StandardOutputContent" \
  --output text | tail -30
```

Expected output ends with something like:
```
Results: 31 passed, 0 failed in 26.3s — status=passed
Artifacts: s3://eagle-documents-695681773636-dev/smoke-results/2026-02-26T12-00-00Z/test-results/
DynamoDB record written: SMOKE_RUN#2026-02-26T12-00-00Z
pw-exit:0
```

### Browse artifacts

```bash
# List runs (most recent first)
AWS_PROFILE=eagle aws dynamodb query \
  --table-name eagle \
  --key-condition-expression "PK = :pk AND SK = :sk" \
  --expression-attribute-values '{":pk":{"S":"SMOKE_RUN#2026-02-26T12-00-00Z"},":sk":{"S":"METADATA"}}' \
  --region us-east-1

# Scan all smoke runs
AWS_PROFILE=eagle aws dynamodb scan \
  --table-name eagle \
  --filter-expression "begins_with(PK, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"SMOKE_RUN#"}}' \
  --region us-east-1 \
  --query "Items[*].{run:PK.S, status:status.S, passed:passed.N, failed:failed.N, duration:duration.S}"

# List videos for a run
AWS_PROFILE=eagle aws s3 ls \
  s3://eagle-documents-695681773636-dev/smoke-results/ \
  --recursive --region us-east-1 | grep ".webm"
```

---

## Mode 2: Fargate ALB (Quick Check)

Runs locally against the deployed ALB. Requires AWS SSO credentials and `npm ci` already done.

```bash
cd client
just smoke-prod full
```

Or manually:

```bash
cd client
BASE_URL=http://$(aws elbv2 describe-load-balancers \
  --names nci-ea-front-o7mgyip4dvih \
  --query "LoadBalancers[0].DNSName" --output text) \
npx playwright test --project=chromium
```

Prerequisite: active AWS SSO session with `eagle` profile.

---

## Infrastructure Reference

| Resource | Value |
|----------|-------|
| EC2 instance | `i-0390c06d166d18926` (`eagle-runner-dev`) |
| EC2 IAM role | `power-user-eagle-ec2Role-dev` |
| S3 script bucket | `s3://eagle-documents-695681773636-dev/scripts/` |
| Cognito User Pool | `us-east-1_GqZzjtSu9` |
| Cognito Client ID | `50r0sfnqbqq9t96v50knal0esa` |
| DynamoDB table | `eagle` |
| S3 documents bucket | `eagle-documents-695681773636-dev` |
| Playwright browsers | `/root/.cache/ms-playwright` (pre-installed) |
| Repo on EC2 | `/root/eagle/` (branch `dev/greg`) |

### Test credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| Standard | `testuser@example.com` | `EagleTest2024!` | User |
| Admin | `admin@example.com` | `EagleAdmin2024!` | Admin |

---

## Test Files

Located in `client/tests/`:

| File | Description |
|------|-------------|
| `navigation.spec.ts` | Page routing and nav links |
| `intake.spec.ts` | OA intake form |
| `admin-dashboard.spec.ts` | Admin-only views |
| `documents.spec.ts` | Document upload/list |
| `workflows.spec.ts` | Workflow search and management |
| `chat.spec.ts` | AI chat (4 tests incl. agent response, uses `test.slow()`) |

### Auth setup (`global-setup.ts`)

Runs once before all tests. Navigates to `/login` and races between:
- Cognito form appearing → fills credentials, submits (prod/Fargate mode)
- Page redirecting away from `/login` → already authed (dev/docker mode)

Saves storage state to `tests/.auth/user.json` so all tests start authenticated.

---

## S3 as source of truth for EC2 scripts

The EC2 repo (`/root/eagle`) is a local bundle clone without GitHub remote access. So the scripts below are the source of truth **in the repo**, uploaded to S3, and pulled down by `run-smoke.sh` at runtime:

| Local file | S3 key |
|------------|--------|
| `scripts/run-smoke.sh` | `scripts/run-smoke.sh` |
| `client/playwright.config.ts` | `scripts/playwright.config.ts` |
| `client/tests/global-setup.ts` | `scripts/global-setup.ts` |

After editing any of them, re-upload with:

```bash
AWS_PROFILE=eagle aws s3 cp scripts/run-smoke.sh \
  s3://eagle-documents-695681773636-dev/scripts/run-smoke.sh --region us-east-1

AWS_PROFILE=eagle aws s3 cp client/playwright.config.ts \
  s3://eagle-documents-695681773636-dev/scripts/playwright.config.ts --region us-east-1

AWS_PROFILE=eagle aws s3 cp client/tests/global-setup.ts \
  s3://eagle-documents-695681773636-dev/scripts/global-setup.ts --region us-east-1
```

`run-smoke.sh` downloads `playwright.config.ts` and `global-setup.ts` from S3 before each run, so updates take effect immediately without touching the EC2 repo.

---

## DynamoDB Run Record Schema

Written to the `eagle` table after every run:

| Attribute | Type | Example |
|-----------|------|---------|
| `PK` | S | `SMOKE_RUN#2026-02-26T12-00-00Z` |
| `SK` | S | `METADATA` |
| `run_id` | S | `2026-02-26T12-00-00Z` |
| `timestamp` | S | ISO-8601 UTC |
| `status` | S | `passed` or `failed` |
| `passed` | N | `31` |
| `failed` | N | `0` |
| `duration` | S | `26.3s` |
| `pw_exit` | N | `0` |
| `s3_prefix` | S | `s3://eagle-documents-695681773636-dev/smoke-results/{run_id}/test-results/` |
| `ttl` | N | epoch + 90 days (auto-deleted by DynamoDB TTL) |

---

## Troubleshooting

### Tests fail with auth errors / stuck on /login
- Cognito user may not exist. Run: `python scripts/create_users.py`
- Also ensure custom attributes are set:
  ```bash
  aws cognito-idp admin-update-user-attributes \
    --user-pool-id us-east-1_GqZzjtSu9 \
    --username testuser@example.com \
    --user-attributes \
      Name=custom:tenant_id,Value=test-tenant \
      Name=custom:subscription_tier,Value=standard \
    --region us-east-1
  ```

### Docker compose fails to start
- Check if containers are already running: `docker ps`
- Force clean: `docker compose -f deployment/docker-compose.dev.yml down --remove-orphans`

### Backend never ready (wait_for_backend.py times out)
- Check `.env` was written correctly (check IMDSv2 credential fetch)
- Check ECR image pull — the EC2 role needs `ecr:GetAuthorizationToken` and `ecr:BatchGetImage`

### SSM command stuck in InProgress
- 600s timeout is set; chat tests use `test.slow()` (60s each)
- If it's been >10 min, check docker build logs via SSM interactive session

### CRLF errors (`\r': command not found`)
- Always run `sed -i s/\r// /tmp/run-smoke.sh` before executing scripts transferred from Windows

### `strings` command not found
- Amazon Linux 2023 does not have `binutils` by default; remove `| strings` from any output filters

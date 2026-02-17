# EAGLE Local Setup Instructions

## Prerequisites

- **Git** installed
- **Python 3.11+** and **Node.js 18+** (or Docker)
- **Docker Desktop** (if using Option A below) — [install guide](https://docs.docker.com/desktop/)
- **AWS CLI v2** installed ([install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))

---

## 1. Configure AWS Credentials

Run this in your terminal:
```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID:     <sent via Slack DM>
AWS Secret Access Key: <sent via Slack DM>
Default region name:   us-east-1
Default output format: json
```

Verify it works:
```bash
aws sts get-caller-identity
```
You should see `eagle-dev-hoquemi` as the user.

---

## 2. Clone the Repo

```bash
git clone https://github.com/gblack686/sample-multi-tenant-agent-core-app.git
cd sample-multi-tenant-agent-core-app
git checkout dev/greg
```

---

## 3. Create `.env` File

Create a `.env` file in the project root:
```
USE_BEDROCK=true
DEV_MODE=false
REQUIRE_AUTH=true
USE_PERSISTENT_SESSIONS=false
COGNITO_USER_POOL_ID=us-east-1_AZuPs6Ifs
COGNITO_CLIENT_ID=4cv12gt73qi3nct25vl6mno72a
COGNITO_REGION=us-east-1
AWS_REGION=us-east-1
```

No Anthropic API key needed — Claude runs through Bedrock with your AWS credentials.

---

## 4. Run the App

### Option A: Docker (easiest)

Uses `docker-compose.dev.yml` which spins up two containers:

| Container | Base Image | Port | What it does |
|-----------|-----------|------|--------------|
| `backend` | Python 3.11-slim | 8000 | FastAPI + Anthropic SDK agent |
| `frontend` | Node 20-alpine | 3000 | Next.js app (connects to backend internally) |

```bash
docker compose -f docker-compose.dev.yml up --build
```

Then open http://localhost:3000

Source directories are mounted as volumes, so code changes are reflected without rebuilding. To rebuild from scratch:
```bash
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up --build
```

### Option B: Run locally (two terminals)

**Terminal 1 — Backend:**
```bash
cd server
pip install -r requirements.txt
python run.py
```
Backend runs at http://localhost:8000

**Terminal 2 — Frontend:**
```bash
cd client
npm install
npm run dev
```
Frontend runs at http://localhost:3000

---

## 5. Log In

- **Email:** `hoquemi@nih.gov`
- **Password:** `Eagle@NCI2026!`

---

## 6. Key Routes

| Route | Description |
|-------|-------------|
| `/` | EAGLE chat (default) |
| `/admin/eval` | Eval suite results + UC sequence diagrams |

---

## 7. Run the Eval Suite (optional)

```bash
cd server/tests
python test_eagle_sdk_eval.py --model haiku --tests 16,17,18,19,20
```

This runs the AWS tool integration tests (no LLM cost). To run the full 28-test suite:
```bash
python test_eagle_sdk_eval.py --model haiku
```

---

## Project Structure

```
client/           <- Next.js frontend
server/           <- Python backend (FastAPI + Anthropic SDK)
  app/            <- Main app code (agentic_service.py, sdk_agentic_service.py)
  tests/          <- Eval suite (28 tests)
eagle-plugin/     <- EAGLE plugin (skills + prompts)
infra/            <- CDK + Terraform
data/             <- Media, eval results, traces
```

---

## AWS Services Your Credentials Access

| Service | Resource | Purpose |
|---------|----------|---------|
| Bedrock | Claude Haiku/Sonnet | LLM inference |
| S3 | `nci-documents` | Document storage |
| S3 | `eagle-eval-artifacts` | Eval results archival |
| DynamoDB | `eagle` table | Intake records |
| CloudWatch | `/eagle/*` log groups | App + eval logs |
| CloudWatch | `EAGLE/Eval` namespace | Eval metrics |

---

Questions? Ping me on Slack.

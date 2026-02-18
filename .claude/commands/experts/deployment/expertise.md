---
type: expert-file
parent: "[[deployment/_index]]"
file-type: expertise
human_reviewed: false
tags: [expert-file, mental-model, deployment, aws, cdk]
last_updated: 2026-02-18T12:15:00
---

# Deployment Expertise (Complete Mental Model)

> **Sources**: AWS Console (manual resources), nci-oa-agent CDK patterns, Next.js documentation, GitHub Actions OIDC docs

---

## Part 1: Current Infrastructure

### Provisioning Model

Infrastructure is managed by **4 CDK stacks** in `infrastructure/cdk-eagle/` (TypeScript). Some resources (S3 `nci-documents`, DynamoDB `eagle`, Bedrock access) were manually provisioned and are imported by CDK.

```
Provisioning: CDK-managed (4 stacks) + manually-created imported resources
Region: us-east-1
Account: 274487662938
CDK: infrastructure/cdk-eagle/ (TypeScript)
  - EagleCiCdStack:    GitHub Actions OIDC + deploy role
  - EagleCoreStack:    VPC, Cognito, IAM app role, imports S3/DDB
  - EagleComputeStack: ECR repos, ECS Fargate, ALB, auto-scaling
  - EagleEvalStack:    S3 eval artifacts, CloudWatch dashboard, SNS alerts
CI/CD: GitHub Actions (OIDC → ECR push → ECS deploy)
Docker: Dockerfile.backend + Dockerfile.frontend in deployment/docker/
```

### Credential Configuration

```
~/.aws/credentials
  |-- [default] or named profile
  |-- aws_access_key_id = AKIA...
  |-- aws_secret_access_key = ...
  |-- region = us-east-1

~/.aws/config
  |-- [default]
  |-- region = us-east-1
  |-- output = json
```

**Access pattern**: All code (eval suite, agentic_service, boto3 checks) uses `boto3.client('service', region_name='us-east-1')` — hardcoded region, default credential chain.

### What Exists (Deployed)

| Component | Resource | Managed By |
|-----------|----------|------------|
| VPC | `vpc-0ede565d9119f98aa` (2 AZs, 1 NAT) | CDK (EagleCoreStack) |
| Cognito User Pool | `us-east-1_fyy3Ko0tX` | CDK (EagleCoreStack) |
| Cognito App Client | `7jlpjkiov7888kcbu57jcn68no` | CDK (EagleCoreStack) |
| IAM App Role | `eagle-app-role-dev` | CDK (EagleCoreStack) |
| S3 `nci-documents` | Document storage | Manual (imported by CDK) |
| DynamoDB `eagle` | Single-table design | Manual (imported by CDK) |
| ECR `eagle-backend-dev` | Backend container registry | CDK (EagleComputeStack) |
| ECR `eagle-frontend-dev` | Frontend container registry | CDK (EagleComputeStack) |
| ECS cluster `eagle-dev` | Fargate cluster | CDK (EagleComputeStack) |
| ECS `eagle-backend-dev` | Backend service (1 task) | CDK (EagleComputeStack) |
| ECS `eagle-frontend-dev` | Frontend service (1 task) | CDK (EagleComputeStack) |
| ALB (frontend) | Public-facing | CDK (EagleComputeStack) |
| ALB (backend) | Internal | CDK (EagleComputeStack) |
| S3 `eagle-eval-artifacts` | Eval results archive | CDK (EagleEvalStack) |
| SNS `eagle-eval-alerts-dev` | Eval alerting | CDK (EagleEvalStack) |
| CW Dashboard `EAGLE-Eval-Dashboard-dev` | Eval metrics | CDK (EagleEvalStack) |
| CW Alarm `eagle-eval-pass-rate-dev` | Pass rate < 80% | CDK (EagleEvalStack) |
| CW Log Group `/eagle/test-runs` | Eval logs | Auto-created (imported by CDK) |
| GitHub Actions OIDC | Federation provider | CDK (EagleCiCdStack) |
| IAM Deploy Role | `eagle-deploy-role-dev` | CDK (EagleCiCdStack) |
| Bedrock model access | Anthropic Claude (Haiku, Sonnet, Opus) | Manual (AWS Console) |

### Live URLs

| Service | URL |
|---------|-----|
| Frontend (public) | `http://EagleC-Front-XYyWWR29wzVZ-745394335.us-east-1.elb.amazonaws.com` |
| Backend (internal) | `http://internal-EagleC-Backe-6OVxEGWRMzba-362151769.us-east-1.elb.amazonaws.com` |

---

## Part 2: AWS Resources Inventory

### S3 Bucket: `nci-documents`

```
Bucket: nci-documents
Region: us-east-1
Versioning: Unknown (likely disabled)
Encryption: Unknown (likely SSE-S3 default)
Public Access: Likely blocked (default)

Key Structure:
  eagle/{tenant_id}/{user_id}/                    # User workspace root
  eagle/{tenant_id}/{user_id}/documents/           # Generated documents
  eagle/{tenant_id}/{user_id}/documents/{type}_{timestamp}.md

Example:
  eagle/demo-tenant/demo-user/documents/sow_20260209T120000.md
```

**Used by**:
- `server/app/agentic_service.py` — `_exec_s3_document_ops()` for read/write/list/delete
- `server/app/agentic_service.py` — `_exec_create_document()` for saving generated docs
- `server/tests/test_eagle_sdk_eval.py` — Tests 16 and 19 (with cleanup)

### DynamoDB Table: `eagle`

```
Table: eagle
Region: us-east-1
Billing: Unknown (likely on-demand)
Key Schema:
  PK (String) - Partition Key
  SK (String) - Sort Key

Access Patterns:
  PK=INTAKE#{tenant_id}, SK=INTAKE#{item_id}  ->  Intake records
  PK=INTAKE#{tenant_id}, SK begins_with INTAKE#  ->  List by tenant

GSI: Unknown (may not have any)
```

**Used by**:
- `server/app/agentic_service.py` — `_exec_dynamodb_intake()` for create/read/update/list/delete
- `server/tests/test_eagle_sdk_eval.py` — Test 17 (with cleanup)

### S3 Bucket: `eagle-eval-artifacts` (CDK-managed)

```
Bucket: eagle-eval-artifacts
Region: us-east-1
Encryption: SSE-S3
Public Access: Blocked
Lifecycle: 365-day expiration
Removal Policy: RETAIN
CDK Stack: EagleEvalStack

Key Structure:
  eval/results/run-{ISO8601_timestamp}.json    # Eval results JSON
  eval/videos/{run-ts}/{test_dir}/{file}       # Video recordings (.webm/.mp4)
```

**Used by**:
- `server/tests/eval_aws_publisher.py` — `archive_results_to_s3()` and `archive_videos_to_s3()`

### CloudWatch Log Group: `/eagle/test-runs`

```
Log Group: /eagle/test-runs
Region: us-east-1
Retention: 90 days (CDK-managed)
CDK Stack: EagleEvalStack

Stream Naming: run-{ISO8601_timestamp}Z
  Example: run-2026-02-09T12:00:00Z

Event Types:
  - test_result (one per test, per run)
  - run_summary (one per run, final event)
```

**Used by**:
- `server/tests/test_eagle_sdk_eval.py` — `emit_to_cloudwatch()` writes structured events
- `server/app/agentic_service.py` — `_exec_cloudwatch_logs()` reads log data
- `server/tests/test_eagle_sdk_eval.py` — Tests 18 and 20 (read-only verification)

### CloudWatch Custom Metrics: `EAGLE/Eval` (CDK-managed)

```
Namespace: EAGLE/Eval
CDK Stack: EagleEvalStack

Metrics:
  PassRate (Percent)           — aggregate and per-RunId dimension
  TestsPassed (Count)          — aggregate
  TestsFailed (Count)          — aggregate
  TestsSkipped (Count)         — aggregate
  TotalCost (None)             — aggregate, only if > 0
  TestStatus (None, 1.0/0.0)  — per-TestName dimension (27 tests)

Dashboard: EAGLE-Eval-Dashboard
Alarm: EvalPassRate (< 80% threshold, SNS action)
```

**Used by**:
- `server/tests/eval_aws_publisher.py` — `publish_eval_metrics()` emits via put_metric_data

### SNS Topic: `eagle-eval-alerts` (CDK-managed)

```
Topic: eagle-eval-alerts
Display Name: EAGLE Eval Alerts
Region: us-east-1
CDK Stack: EagleEvalStack
```

**Used by**:
- CloudWatch Alarm `EvalPassRate` — triggers SNS when pass rate drops below 80%

### Bedrock: Anthropic Models

```
Service: Amazon Bedrock
Region: us-east-1
Provider: Anthropic
Models Used:
  - Claude Haiku (primary for eval suite via --model haiku)
  - Potentially Claude Sonnet/Opus for production

Access: Enabled via AWS Console -> Bedrock -> Model Access
Auth: Same AWS credentials as other services
```

**Used by**:
- `claude-agent-sdk` — `query()` calls route through Bedrock
- `server/tests/test_eagle_sdk_eval.py` — Tests 1-15 (SDK and skill tests)

---

## Part 3: Next.js Deployment Options

### Option A: Static Export (S3 + CloudFront)

```
Build: next build && next export (or output: 'export' in next.config.js)
Host: S3 bucket (static website hosting)
CDN: CloudFront distribution
SSL: ACM certificate (us-east-1 for CloudFront)
DNS: Route 53 (optional)

Pros:
  - Cheapest option (S3 + CloudFront pricing)
  - No server to manage
  - Global CDN distribution
  - Simple deployment (sync files to S3)

Cons:
  - No API routes (must use separate API)
  - No SSR or ISR
  - No middleware
  - Must handle client-side auth differently

Build Command:
  cd client && npm run build
  # Produces out/ directory with static files

Deploy Command:
  aws s3 sync out/ s3://{bucket-name}/ --delete
  aws cloudfront create-invalidation --distribution-id {id} --paths "/*"
```

### Option B: Standalone (ECS Fargate)

```
Build: next build (with output: 'standalone' in next.config.js)
Host: ECS Fargate task
Registry: ECR
Load Balancer: ALB (Application Load Balancer)
SSL: ACM certificate (on ALB)
DNS: Route 53 (optional)

Pros:
  - Full Next.js features (API routes, SSR, ISR, middleware)
  - Container-based (reproducible, scalable)
  - Can colocate API and frontend

Cons:
  - More expensive (ECS Fargate pricing)
  - More complex infrastructure (VPC, ALB, ECS, ECR)
  - Requires Docker build pipeline
  - Cold start latency (Fargate startup)

Build Command:
  docker build -t eagle-frontend .
  # Multi-stage Dockerfile produces minimal standalone image

Deploy Command:
  # Push to ECR, update ECS service
  aws ecr get-login-password | docker login --username AWS --password-stdin {account}.dkr.ecr.us-east-1.amazonaws.com
  docker tag eagle-frontend:latest {account}.dkr.ecr.us-east-1.amazonaws.com/eagle-frontend:latest
  docker push {account}.dkr.ecr.us-east-1.amazonaws.com/eagle-frontend:latest
  aws ecs update-service --cluster eagle --service frontend --force-new-deployment
```

### Decision Criteria

| Factor | Static Export | ECS Standalone |
|--------|-------------|----------------|
| API routes used? | No -> Static | Yes -> ECS |
| SSR needed? | No -> Static | Yes -> ECS |
| Budget | Low -> Static | Higher -> ECS |
| Complexity tolerance | Low -> Static | Higher -> ECS |
| Auth model | Client-side -> Static | Server-side -> ECS |

### Current Project Assessment

**Active deployment: ECS Fargate Standalone** (Option B).

The `client/` directory uses API routes (`app/api/`), SSR, and Cognito auth — all require a server. The frontend runs as a standalone Next.js server on ECS Fargate behind a public ALB.

---

## Part 4: CDK Patterns

### Active CDK Stacks (infrastructure/cdk-eagle/)

All 4 stacks live in `infrastructure/cdk-eagle/` and deploy from `bin/eagle.ts`.

#### EagleCiCdStack (independent)

```
File: lib/cicd-stack.ts
Resources:
  - OIDC Provider: token.actions.githubusercontent.com
  - IAM Deploy Role: eagle-deploy-role-dev (trusted by gblack686/sample-multi-tenant-agent-core-app)
Outputs: eagle-deploy-role-arn-dev
```

#### EagleCoreStack (independent)

```
File: lib/core-stack.ts
Resources:
  - VPC: 2 AZs, 1 NAT Gateway, public + private subnets
  - Cognito User Pool + App Client
  - IAM App Role: eagle-app-role-dev (S3, DynamoDB, Bedrock, CloudWatch, Logs)
  - CloudWatch Log Group: /eagle/app
  - Imports: S3 nci-documents, DynamoDB eagle (fromBucketName/fromTableName)
Outputs: eagle-vpc-id-dev, eagle-user-pool-id-dev, eagle-user-pool-client-id-dev, eagle-app-role-arn-dev
```

#### EagleComputeStack (depends on Core)

```
File: lib/compute-stack.ts
Resources:
  - ECR: eagle-backend-dev, eagle-frontend-dev
  - ECS Cluster: eagle-dev (Fargate)
  - Backend Service: 512 CPU / 1024 MB, port 8000, internal ALB
  - Frontend Service: 256 CPU / 512 MB, port 3000, public ALB
  - Auto-scaling: 1-4 tasks (CPU target 70%)
Outputs: eagle-backend-repo-uri-dev, eagle-frontend-repo-uri-dev, eagle-cluster-name-dev
```

#### EagleEvalStack (independent)

```
File: lib/eval-stack.ts
Resources:
  - S3 Bucket: eagle-eval-artifacts (365-day lifecycle, SSE-S3, RETAIN)
  - SNS Topic: eagle-eval-alerts-dev
  - CW Alarm: eagle-eval-pass-rate-dev (< 80% → SNS)
  - CW Dashboard: EAGLE-Eval-Dashboard-dev (28 per-test widgets)
  - Imports: LogGroup /eagle/test-runs (fromLogGroupName, not created)
Outputs: eagle-eval-bucket-name-dev, eagle-eval-bucket-arn-dev, eagle-eval-alert-topic-arn-dev, etc.
```

#### Legacy Stacks (not deployed)

```
infrastructure/eval/  — Standalone EvalObservabilityStack (SUPERSEDED by EagleEvalStack above)
infrastructure/cdk/   — Python reference stack (never deployed)
```

### Reference Stack Structure Convention (nci-oa-agent)

```
cdk/
  |-- bin/
  |     |-- app.ts                    # CDK app entry point
  |
  |-- lib/
  |     |-- stacks/
  |     |     |-- storage-stack.ts     # S3, DynamoDB
  |     |     |-- compute-stack.ts     # ECS, Fargate, ECR
  |     |     |-- network-stack.ts     # VPC, ALB, CloudFront
  |     |     |-- monitoring-stack.ts  # CloudWatch, alarms
  |     |     |-- auth-stack.ts        # Cognito, IAM roles
  |     |     |-- pipeline-stack.ts    # CodePipeline (optional)
  |     |
  |     |-- constructs/
  |     |     |-- next-frontend.ts     # Reusable Next.js deployment construct
  |     |     |-- eagle-table.ts       # DynamoDB with standard key schema
  |     |
  |     |-- config/
  |           |-- environments.ts      # dev/staging/prod config
  |
  |-- cdk.json                         # CDK configuration
  |-- tsconfig.json                    # TypeScript config for CDK
  |-- package.json                     # CDK dependencies
```

### Naming Conventions (nci-oa-agent pattern)

```typescript
// Stack names: {project}-{component}-{env}
const stackName = `eagle-storage-${env}`;
const stackName = `eagle-compute-${env}`;

// Resource names: {project}-{resource}-{env}
const bucketName = `eagle-documents-${env}`;   // NOT "nci-documents"
const tableName = `eagle-table-${env}`;         // NOT just "eagle"

// Tags: applied to all resources
Tags.of(this).add('Project', 'eagle');
Tags.of(this).add('Environment', env);
Tags.of(this).add('ManagedBy', 'cdk');
```

### Config System

```typescript
// lib/config/environments.ts
interface EnvironmentConfig {
  account: string;
  region: string;
  stage: 'dev' | 'staging' | 'prod';
  domainName?: string;
  certificateArn?: string;
  vpcId?: string;
}

const environments: Record<string, EnvironmentConfig> = {
  dev: {
    account: '123456789012',
    region: 'us-east-1',
    stage: 'dev',
  },
  prod: {
    account: '123456789012',
    region: 'us-east-1',
    stage: 'prod',
    domainName: 'eagle.example.com',
    certificateArn: 'arn:aws:acm:us-east-1:...',
  },
};
```

### CDK Bootstrap

```bash
# Required once per account/region before first deploy
npx cdk bootstrap aws://{ACCOUNT_ID}/us-east-1

# Produces: CDKToolkit stack with:
#   - S3 staging bucket
#   - ECR staging repository
#   - IAM roles for CDK deployment
```

### Importing Existing Resources

Since resources already exist (manually created), CDK must import them rather than create new ones:

```typescript
// Import existing S3 bucket (read-only reference, CDK won't manage it)
const existingBucket = s3.Bucket.fromBucketName(this, 'ExistingBucket', 'nci-documents');

// Import existing DynamoDB table
const existingTable = dynamodb.Table.fromTableName(this, 'ExistingTable', 'eagle');

// OR: Full import (CDK manages the resource going forward)
// Requires `cdk import` command and resource identifiers
```

---

## Part 5: Docker Patterns

### Multi-Stage Build for Next.js Standalone

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY client/package.json client/package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY client/ .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

# Stage 3: Runtime
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
# CRITICAL: Required for ECS Fargate (binds to all interfaces)
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy standalone output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
```

### Next.js Standalone Configuration

```javascript
// client/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // Produces minimal server.js + dependencies
  // OR
  output: 'export',      // Produces static out/ directory
};

module.exports = nextConfig;
```

### Docker Build Commands

```bash
# Build image
docker build -t eagle-frontend -f Dockerfile .

# Run locally (testing)
docker run -p 3000:3000 eagle-frontend

# Tag for ECR
docker tag eagle-frontend:latest {account}.dkr.ecr.us-east-1.amazonaws.com/eagle-frontend:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {account}.dkr.ecr.us-east-1.amazonaws.com
docker push {account}.dkr.ecr.us-east-1.amazonaws.com/eagle-frontend:latest
```

### Key Docker Considerations

- **HOSTNAME=0.0.0.0**: Required for ECS Fargate. Without it, Next.js binds to `localhost` and is unreachable from the ALB health check.
- **curl for health checks**: Alpine doesn't include `curl`. Add `RUN apk add --no-cache curl` in the runner stage — ECS health check uses `curl -f http://localhost:3000/`.
- **Build args for Cognito**: Frontend needs `--build-arg NEXT_PUBLIC_COGNITO_USER_POOL_ID=... --build-arg NEXT_PUBLIC_COGNITO_CLIENT_ID=...` at build time (NEXT_PUBLIC_* are baked in by Next.js).
- **Multi-stage builds**: Keep final image small (~150MB vs ~1GB for full node_modules).
- **node:20-alpine**: Use Alpine for smallest base image. Match Node version to local development.
- **.dockerignore**: Exclude `node_modules`, `.next`, `.git`, `*.md` from build context. Without it, Docker context transfer is ~800MB+.

---

## Part 6: CI/CD Patterns (GitHub Actions with OIDC)

### OIDC Authentication (No Static Keys)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  id-token: write   # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::{ACCOUNT_ID}:role/github-actions-deploy
          aws-region: us-east-1

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: client/package-lock.json

      - name: Install Dependencies
        run: cd client && npm ci

      - name: Build
        run: cd client && npm run build

      - name: Deploy to S3 (static export)
        run: |
          aws s3 sync client/out/ s3://eagle-frontend-${{ env.STAGE }}/ --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} --paths "/*"
```

### OIDC Trust Policy (IAM)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::{ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:{OWNER}/{REPO}:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

### Docker Build + ECR Push Workflow

```yaml
# .github/workflows/build-push.yml
name: Build and Push

on:
  push:
    branches: [main]
    paths:
      - 'client/**'
      - 'Dockerfile'

permissions:
  id-token: write
  contents: read

jobs:
  build-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::{ACCOUNT_ID}:role/github-actions-deploy
          aws-region: us-east-1

      - name: Login to ECR
        id: ecr-login
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and Push
        env:
          REGISTRY: ${{ steps.ecr-login.outputs.registry }}
          REPOSITORY: eagle-frontend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $REGISTRY/$REPOSITORY:$IMAGE_TAG -t $REGISTRY/$REPOSITORY:latest .
          docker push $REGISTRY/$REPOSITORY:$IMAGE_TAG
          docker push $REGISTRY/$REPOSITORY:latest

      - name: Update ECS Service
        run: |
          aws ecs update-service \
            --cluster eagle \
            --service frontend \
            --force-new-deployment
```

### CDK Deploy Workflow

```yaml
# .github/workflows/cdk-deploy.yml
name: CDK Deploy

on:
  push:
    branches: [main]
    paths:
      - 'cdk/**'

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::{ACCOUNT_ID}:role/github-actions-cdk
          aws-region: us-east-1

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install CDK
        run: npm install -g aws-cdk && cd cdk && npm ci

      - name: CDK Diff
        run: cd cdk && npx cdk diff

      - name: CDK Deploy
        run: cd cdk && npx cdk deploy --all --require-approval never
```

---

## Part 7: Known Issues and Troubleshooting

### CDK Bootstrap Required

**Issue**: `cdk deploy` fails with "This stack uses assets, so the toolkit stack must be deployed"

**Fix**:
```bash
npx cdk bootstrap aws://{ACCOUNT_ID}/us-east-1
```

**When**: Before the very first CDK deployment in any account/region pair.

### VPC Lookup Fails in CI/CD

**Issue**: `Vpc.fromLookup()` fails in GitHub Actions because it requires actual AWS API calls during synthesis.

**Fix**: Use explicit VPC ID in config instead of lookup:
```typescript
// Bad: requires API call during synthesis
const vpc = ec2.Vpc.fromLookup(this, 'Vpc', { isDefault: true });

// Good: explicit ID from config
const vpc = ec2.Vpc.fromVpcAttributes(this, 'Vpc', {
  vpcId: config.vpcId,
  availabilityZones: ['us-east-1a', 'us-east-1b'],
});
```

### HOSTNAME Override for ECS

**Issue**: Next.js standalone binds to `localhost` by default, making it unreachable from ALB health checks in ECS.

**Fix**: Set `HOSTNAME=0.0.0.0` in Dockerfile or ECS task definition:
```dockerfile
ENV HOSTNAME=0.0.0.0
```

Or in ECS task definition:
```json
{
  "environment": [
    { "name": "HOSTNAME", "value": "0.0.0.0" },
    { "name": "PORT", "value": "3000" }
  ]
}
```

### S3 Static Website Routing

**Issue**: Direct URL access to Next.js routes returns 403/404 from S3.

**Fix**: Configure CloudFront error pages to redirect to `index.html` for SPA routing:
```typescript
const distribution = new cloudfront.Distribution(this, 'Dist', {
  errorResponses: [
    {
      httpStatus: 403,
      responseHttpStatus: 200,
      responsePagePath: '/index.html',
      ttl: Duration.minutes(5),
    },
    {
      httpStatus: 404,
      responseHttpStatus: 200,
      responsePagePath: '/index.html',
      ttl: Duration.minutes(5),
    },
  ],
});
```

### Existing Resource Conflict

**Issue**: CDK tries to create a resource that already exists (e.g., S3 bucket `nci-documents`, DynamoDB table `eagle`).

**Fix**: Import existing resources instead of creating new ones:
```typescript
// Reference only (CDK does not manage lifecycle)
const bucket = s3.Bucket.fromBucketName(this, 'Bucket', 'nci-documents');

// Full import (CDK manages lifecycle going forward)
// Run: cdk import EagleStorageStack/Bucket
```

### CloudWatch Log Group Already Exists

**Issue**: CDK creates a log group that the eval suite already auto-created.

**Fix**: Use `removalPolicy: RETAIN` and set `logGroupName` explicitly, or import:
```typescript
// Option 1: Import
const logGroup = logs.LogGroup.fromLogGroupName(this, 'TestRuns', '/eagle/test-runs');

// Option 2: Create with RETAIN (handles if already exists via custom resource)
const logGroup = new logs.LogGroup(this, 'TestRuns', {
  logGroupName: '/eagle/test-runs',
  retention: logs.RetentionDays.THIRTY_DAYS,
  removalPolicy: cdk.RemovalPolicy.RETAIN,
});
```

### AWS Credentials Not Found

**Issue**: boto3 calls fail with `NoCredentialsError` or `InvalidClientTokenId`.

**Fix**:
```bash
# Check current identity
aws sts get-caller-identity

# If no credentials, configure:
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

### Bedrock Model Access Not Enabled

**Issue**: Bedrock API returns `AccessDeniedException` for Anthropic models.

**Fix**: Enable model access in AWS Console:
1. Go to Amazon Bedrock console (us-east-1)
2. Navigate to Model Access
3. Request access to Anthropic Claude models
4. Wait for approval (usually instant for Haiku)

---

## Part 8: Complete Environment Setup Guide (New Account/Region)

This is a step-by-step guide to deploy the full EAGLE platform from scratch in a new AWS environment.

### Prerequisites

```
- AWS CLI configured with credentials for the target account
- Node.js 20+, npm
- Docker Desktop running
- Python 3.11+ with pip
- Git (clone the repo)
```

### Step 1: Bootstrap CDK

```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# Bootstrap CDK (one-time per account/region)
npx cdk bootstrap aws://${ACCOUNT_ID}/${REGION}
```

### Step 2: Create Pre-requisite Resources (Manual)

These resources are imported (not created) by CDK:

```bash
# Create S3 bucket for documents
aws s3 mb s3://nci-documents --region us-east-1

# Create DynamoDB eagle table (single-table design)
aws dynamodb create-table \
  --table-name eagle \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Enable Bedrock model access
# Go to AWS Console → Amazon Bedrock → Model Access → Enable Anthropic Claude models
```

### Step 3: Update CDK Config for New Environment

Edit `infrastructure/cdk-eagle/config/environments.ts`:

```typescript
export const NEW_ENV_CONFIG: EagleConfig = {
  env: 'dev',                           // or 'staging', 'prod'
  account: 'YOUR_ACCOUNT_ID',
  region: 'us-east-1',
  eagleTableName: 'eagle',
  docsBucketName: 'nci-documents',
  evalBucketName: 'eagle-eval-artifacts',
  vpcMaxAzs: 2,
  natGateways: 1,
  backendCpu: 512,
  backendMemory: 1024,
  frontendCpu: 256,
  frontendMemory: 512,
  desiredCount: 1,
  maxCount: 4,
  githubOwner: 'YOUR_GITHUB_ORG',
  githubRepo: 'YOUR_REPO_NAME',
};
```

### Step 4: Deploy All CDK Stacks

```bash
cd infrastructure/cdk-eagle

# Install dependencies
npm install

# Verify templates compile
npx cdk synth

# Deploy all 4 stacks (CiCd and Eval are independent, Core before Compute)
npx cdk deploy EagleCiCdStack --require-approval never
npx cdk deploy EagleCoreStack --require-approval never
npx cdk deploy EagleComputeStack --require-approval never
npx cdk deploy EagleEvalStack --require-approval never

# Record outputs (needed for Docker build args)
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name EagleCoreStack \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name EagleCoreStack \
  --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text)
BACKEND_REPO=$(aws cloudformation describe-stacks --stack-name EagleComputeStack \
  --query "Stacks[0].Outputs[?OutputKey=='BackendRepoUri'].OutputValue" --output text)
FRONTEND_REPO=$(aws cloudformation describe-stacks --stack-name EagleComputeStack \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendRepoUri'].OutputValue" --output text)
```

### Step 5: Build and Push Docker Images

```bash
cd /path/to/repo

# Login to ECR
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -f deployment/docker/Dockerfile.backend \
  -t ${BACKEND_REPO}:latest .
docker push ${BACKEND_REPO}:latest

# Build and push frontend (MUST pass Cognito build args)
docker build -f deployment/docker/Dockerfile.frontend \
  --build-arg NEXT_PUBLIC_COGNITO_USER_POOL_ID=${USER_POOL_ID} \
  --build-arg NEXT_PUBLIC_COGNITO_CLIENT_ID=${CLIENT_ID} \
  -t ${FRONTEND_REPO}:latest .
docker push ${FRONTEND_REPO}:latest
```

**IMPORTANT**: The Dockerfile.frontend MUST include `RUN apk add --no-cache curl` in the runner stage. Without it, the ECS health check (`curl -f http://localhost:3000/`) fails and the task cycles endlessly.

### Step 6: Force ECS Redeployment

```bash
aws ecs update-service --cluster eagle-dev --service eagle-backend-dev --force-new-deployment
aws ecs update-service --cluster eagle-dev --service eagle-frontend-dev --force-new-deployment

# Wait for services to stabilize (~2-5 minutes)
aws ecs wait services-stable --cluster eagle-dev --services eagle-backend-dev eagle-frontend-dev
```

### Step 7: Create Cognito User

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username user@example.com \
  --user-attributes Name=email,Value=user@example.com Name=email_verified,Value=true \
  --temporary-password 'TempPass123!' \
  --message-action SUPPRESS

# Set permanent password (skip FORCE_CHANGE_PASSWORD)
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username user@example.com \
  --password 'YourPassword123!' \
  --permanent
```

### Step 8: Verify Everything Works

```bash
# Get frontend URL
FRONTEND_URL=$(aws cloudformation describe-stacks --stack-name EagleComputeStack \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" --output text)
echo "Frontend: ${FRONTEND_URL}"

# Check ECS services are healthy
aws ecs describe-services --cluster eagle-dev \
  --services eagle-backend-dev eagle-frontend-dev \
  --query "services[].{name:serviceName,running:runningCount,desired:desiredCount}" \
  --output table

# Run eval test 1 to verify S3 archive and CloudWatch
python -u server/tests/test_eagle_sdk_eval.py --tests 1
# Should see: "S3 Archive: uploaded results to s3://eagle-eval-artifacts/..."
```

### Deployment Timing (Observed)

| Step | Time |
|------|------|
| CDK bootstrap | ~2 min |
| CDK deploy (all 4 stacks) | ~5-10 min |
| Docker build (backend) | ~30 sec (cached) |
| Docker build (frontend) | ~60 sec (cached), ~5 min (cold) |
| Docker push (both) | ~1-2 min |
| ECS redeployment | ~2-5 min |
| **Total (cold)** | **~20-25 min** |

---

## Learnings

### patterns_that_work
- Manual provisioning works for dev/prototyping but doesn't scale
- boto3 inline checks (like check-aws command) give instant connectivity feedback
- Hardcoded region `us-east-1` avoids misconfiguration across tools
- TypeScript CDK with `commonjs` module + `node` moduleResolution works reliably with ts-node (discovered: 2026-02-10, component: infrastructure/eval)
- Single-stack pattern for eval observability keeps related resources together — S3, CW dashboard, alarm, SNS in one EvalObservabilityStack (discovered: 2026-02-10, component: infrastructure/eval)
- Python publisher with lazy-loaded boto3 clients and try/except wrappers makes AWS integration non-fatal — eval suite runs fine without credentials (discovered: 2026-02-10, component: eval_aws_publisher)
- Import-guard pattern (`try: import ... except ImportError: _HAS_FLAG = False`) keeps optional AWS modules zero-impact (discovered: 2026-02-10, component: test_eagle_sdk_eval)
- CDK context flags copied from existing `infrastructure/cdk/cdk.json` ensure consistent behavior across stacks (discovered: 2026-02-10, component: infrastructure/eval)
- Merging eval stack into main CDK app (4th stack, independent, no cross-stack deps) ensures it deploys with everything else — no more orphaned standalone stacks (discovered: 2026-02-17, component: infrastructure/cdk-eagle)
- Using `LogGroup.fromLogGroupName()` instead of `new LogGroup()` avoids conflicts with auto-created log groups from the eval suite (discovered: 2026-02-17, component: eval-stack)
- Config-driven bucket names (`config.evalBucketName`) with env defaults matching the publisher means zero code changes needed for the eval suite (discovered: 2026-02-17, component: eval-stack)
- ECS deployment takes ~41s for a lightweight stack (S3 + SNS + CW alarm + dashboard) (discovered: 2026-02-17, component: EagleEvalStack)
- Justfile with Python boto3 for AWS operations — `aws` CLI returns exit code 1 on MSYS/Git Bash even when succeeding; boto3 is reliable cross-platform (discovered: 2026-02-18, component: Justfile)
- `build-frontend` recipe auto-fetches Cognito config from CDK stack outputs via boto3 — no hardcoded pool IDs (discovered: 2026-02-18, component: Justfile)
- Internal just recipes prefixed with `_` stay hidden from `just --list` — clean separation of public and private commands (discovered: 2026-02-18, component: Justfile)

### patterns_to_avoid
- Don't create new CDK resources that conflict with existing manual resources
- Don't use `Vpc.fromLookup()` in CI/CD pipelines (synthesis-time API call)
- Don't forget HOSTNAME=0.0.0.0 for containerized Next.js
- Don't use `NodeNext` module/moduleResolution in tsconfig when using ts-node with CDK — causes `Cannot find module '../lib/eval-stack.js'` errors; use `commonjs`/`node` instead (discovered: 2026-02-10, component: infrastructure/eval)
- Don't append `.js` extension to TypeScript imports in CDK projects using commonjs module — ts-node resolves `.ts` files directly (discovered: 2026-02-10, component: infrastructure/eval)
- Don't use `node:20-alpine` for ECS Fargate containers with `curl` health checks without installing curl — Alpine doesn't include it. Add `RUN apk add --no-cache curl` (discovered: 2026-02-17, component: Dockerfile.frontend)
- Don't forget Cognito `--build-arg` when building frontend Docker image — NEXT_PUBLIC_* vars are baked in at build time, not runtime (discovered: 2026-02-17, component: Dockerfile.frontend)
- Don't keep eval observability in a standalone CDK project — it gets forgotten and never deployed. Merge into the main CDK app (discovered: 2026-02-17, component: infrastructure/eval → cdk-eagle)
- Don't use `aws` CLI in Justfile shebang scripts on Windows/MSYS — exit code 1 even on success breaks `set -euo pipefail`. Use Python boto3 instead (discovered: 2026-02-18, component: Justfile)
- Don't hardcode ALB URLs in task runners — they change on redeployment. Fetch dynamically from `describe_load_balancers()` (discovered: 2026-02-18, component: Justfile)

### common_issues
- AWS credentials expire or are not configured -> all services fail
- S3 bucket name globally unique constraint -> can't reuse names across accounts
- CDK bootstrap missing -> deploy fails with cryptic asset error
- `Cannot find module '../lib/eval-stack.js'`: caused by NodeNext moduleResolution + .js import extension with ts-node; fix by switching to commonjs module and removing .js extension (component: infrastructure/eval)
- CloudWatch log group `/eagle/test-runs` may already exist when CDK tries to create it: use `LogGroup.fromLogGroupName()` to import instead (component: eval-stack)
- ECS frontend health check fails with `curl: not found`: Alpine-based node images don't include curl. Fix: `RUN apk add --no-cache curl` in Dockerfile runner stage (component: Dockerfile.frontend)
- ECS service shows 2 deployments with old tasks draining after force-new-deployment: this is normal, wait 2-5 min for the old tasks to drain (component: ECS)
- Docker context transfer is ~800MB+ without .dockerignore: ensure `.dockerignore` excludes `node_modules`, `.next`, `.git`, `data/` (component: Dockerfile.frontend)

### tips
- Run `/experts:deployment:maintenance` before any deployment to verify connectivity
- Tag all CDK resources with Project=eagle and ManagedBy=cdk for cost tracking
- Use OIDC for GitHub Actions instead of static IAM keys (more secure, no rotation needed)
- Run `npx cdk synth` before `cdk deploy` to verify CloudFormation template generates correctly
- All 4 CDK stacks deploy from `infrastructure/cdk-eagle/`: `npx cdk deploy --all`
- Before first deploy, check if `/eagle/test-runs` log group exists: `aws logs describe-log-groups --log-group-name-prefix /eagle/test-runs`
- `put_metric_data` supports up to 1000 metrics per call — our 38 metrics per eval run are well within limits
- Use `aws ecs wait services-stable` after force-new-deployment to block until rollout completes
- Use `--message-action SUPPRESS` when creating Cognito users via CLI to avoid sending emails
- After Cognito user creation, use `admin-set-user-password --permanent` to skip the FORCE_CHANGE_PASSWORD state
- Verify deployment with eval test 1: `python -u server/tests/test_eagle_sdk_eval.py --tests 1` — confirms S3, CloudWatch, and Bedrock connectivity
- Use `just --list` to see all available commands — replaces scattered shell scripts with one entry point
- `just status` / `just urls` / `just check-aws` for quick operational checks
- `just deploy` for full deploy pipeline: ECR login → build → push → ECS update → wait → status
- `just ci` for full CI: lint → test → eval-aws
- `just ship` for full ship: lint → deploy

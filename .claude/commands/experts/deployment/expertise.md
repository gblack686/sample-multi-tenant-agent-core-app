---
type: expert-file
parent: "[[deployment/_index]]"
file-type: expertise
human_reviewed: false
tags: [expert-file, mental-model, deployment, aws, cdk]
last_updated: 2026-02-09T00:00:00
---

# Deployment Expertise (Complete Mental Model)

> **Sources**: AWS Console (manual resources), nci-oa-agent CDK patterns, Next.js documentation, GitHub Actions OIDC docs

---

## Part 1: Current Infrastructure

### Provisioning Model

All AWS resources are **manually provisioned** — no infrastructure-as-code exists. Resources were created via AWS Console or CLI during initial development.

```
Provisioning: Manual (AWS Console / CLI)
Region: us-east-1
Account: Accessed via ~/.aws/credentials (local profile)
IAM: Developer credentials with broad permissions
CDK: Not configured
CI/CD: Not configured
Docker: Not configured
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

### What Exists vs What Doesn't

| Component | Exists | Notes |
|-----------|--------|-------|
| S3 bucket | Yes | `nci-documents`, manually created |
| DynamoDB table | Yes | `eagle`, manually created |
| CloudWatch log group | Yes | `/eagle/test-runs`, auto-created by eval suite |
| Bedrock model access | Yes | Anthropic models enabled in Console |
| CDK project | No | No `cdk.json`, no `lib/`, no stacks |
| Dockerfile | No | No container configuration |
| GitHub Actions | No | No `.github/workflows/` |
| CloudFront distribution | No | Frontend runs locally only |
| ECS cluster/service | No | No container orchestration |
| ECR repository | No | No container registry |
| IAM deployment role | No | No OIDC trust, no CD role |
| VPC | No | All services use default/public endpoints |

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
- `app/agentic_service.py` — `_exec_s3_document_ops()` for read/write/list/delete
- `app/agentic_service.py` — `_exec_create_document()` for saving generated docs
- `test_eagle_sdk_eval.py` — Tests 16 and 19 (with cleanup)

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
- `app/agentic_service.py` — `_exec_dynamodb_intake()` for create/read/update/list/delete
- `test_eagle_sdk_eval.py` — Test 17 (with cleanup)

### CloudWatch Log Group: `/eagle/test-runs`

```
Log Group: /eagle/test-runs
Region: us-east-1
Retention: Unknown (likely indefinite)

Stream Naming: run-{ISO8601_timestamp}Z
  Example: run-2026-02-09T12:00:00Z

Event Types:
  - test_result (one per test, per run)
  - run_summary (one per run, final event)
```

**Used by**:
- `test_eagle_sdk_eval.py` — `emit_to_cloudwatch()` writes structured events
- `app/agentic_service.py` — `_exec_cloudwatch_logs()` reads log data
- `test_eagle_sdk_eval.py` — Tests 18 and 20 (read-only verification)

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
- `test_eagle_sdk_eval.py` — Tests 1-15 (SDK and skill tests)

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
  cd nextjs-frontend && npm run build
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

The `nextjs-frontend/` directory uses:
- API routes (`app/api/prompts/`) -> Needs server
- Auth context (`contexts/auth-context.tsx`) -> Could be client-side
- No confirmed SSR/ISR usage

**Recommendation**: Start with static export for speed, migrate to ECS if API routes become essential.

---

## Part 4: CDK Patterns (from nci-oa-agent)

### Stack Structure Convention

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
COPY nextjs-frontend/package.json nextjs-frontend/package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY nextjs-frontend/ .
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
// nextjs-frontend/next.config.js
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
- **Multi-stage builds**: Keep final image small (~150MB vs ~1GB for full node_modules).
- **node:20-alpine**: Use Alpine for smallest base image. Match Node version to local development.
- **.dockerignore**: Exclude `node_modules`, `.next`, `.git`, `*.md` from build context.

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
          cache-dependency-path: nextjs-frontend/package-lock.json

      - name: Install Dependencies
        run: cd nextjs-frontend && npm ci

      - name: Build
        run: cd nextjs-frontend && npm run build

      - name: Deploy to S3 (static export)
        run: |
          aws s3 sync nextjs-frontend/out/ s3://eagle-frontend-${{ env.STAGE }}/ --delete
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
      - 'nextjs-frontend/**'
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

## Learnings

### patterns_that_work
- Manual provisioning works for dev/prototyping but doesn't scale
- boto3 inline checks (like check-aws command) give instant connectivity feedback
- Hardcoded region `us-east-1` avoids misconfiguration across tools

### patterns_to_avoid
- Don't create new CDK resources that conflict with existing manual resources
- Don't use `Vpc.fromLookup()` in CI/CD pipelines (synthesis-time API call)
- Don't forget HOSTNAME=0.0.0.0 for containerized Next.js

### common_issues
- AWS credentials expire or are not configured -> all services fail
- S3 bucket name globally unique constraint -> can't reuse names across accounts
- CDK bootstrap missing -> deploy fails with cryptic asset error

### tips
- Run `/experts:deployment:maintenance` before any deployment to verify connectivity
- Start with static export (simpler) and migrate to ECS only if API routes are needed
- Tag all CDK resources with Project=eagle and ManagedBy=cdk for cost tracking
- Use OIDC for GitHub Actions instead of static IAM keys (more secure, no rotation needed)

# AWS Resource Cleanup Plan

> **Account**: 274487662938 | **Region**: us-east-1 | **Date**: 2026-02-16

---

## Current Monthly Cost Estimate

| Resource | Service | Monthly Cost | Status | Notes |
|----------|---------|-------------|--------|-------|
| **NAT Gateway** (eagle-vpc-dev) | VPC | **~$32** | KEEP | EagleCoreStack; needed for private subnets |
| **ALB** (EagleComputeStack backend) | ELB | **~$16** | KEEP | Internal, eagle-dev cluster |
| **ALB** (EagleComputeStack frontend) | ELB | **~$16** | KEEP | Public, eagle-dev cluster |
| **ALB** (nci-eagle-dev-frontend-ecs) | ELB | **~$16** | DELETE candidate | OLD stack, 1 running task |
| **Lightsail instance** (openclaw-4gb) | Lightsail | **$24** | YOU DECIDE | Running, medium_3_0, 4GB RAM |
| **Lightsail instance** (multi-agent-adw) | Lightsail | **$5** | DELETE candidate | STOPPED since Oct 2025 |
| **Lightsail container** (nci-eagle) | Lightsail | **$15** | DELETE candidate | Replaced by ECS eagle-dev |
| **ECS Fargate** (eagle-dev backend) | ECS | **~$18** | KEEP | desiredCount=1, not yet running (no image pushed) |
| **ECS Fargate** (eagle-dev frontend) | ECS | **~$9** | KEEP | desiredCount=1, not yet running (no image pushed) |
| **ECS Fargate** (eagle-intake-frontend) | ECS | **~$9** | DELETE candidate | OLD cluster, 1 running task |
| **4 Elastic IPs** (unattached) | EC2 | **~$15** | DELETE | Charged when NOT attached ($3.65/mo each) |
| **Cognito** (multi-tenant-chat-users) | Cognito | $0 | DELETE candidate | Old pool, not used by new stacks |
| **Cognito** (llmopsquickstart x2) | Cognito | $0 | DELETE candidate | Old quickstart pools |
| **Cognito** (graphiti-webshot-users) | Cognito | $0 | DELETE candidate | From graphiti project |
| **Cognito** (eagle-users-dev) | Cognito | $0 | KEEP | EagleCoreStack |
| S3 (gblack686) | S3 | ~$0.40 | REVIEW | 16.5 GB — personal data? |
| S3 (31 buckets total) | S3 | ~$1-2 | REVIEW | Most are small/empty |
| DynamoDB (3 graphiti tables) | DynamoDB | ~$0 | DELETE candidate | On-demand, no traffic = free |
| CloudWatch (56 log groups) | CW | ~$1-3 | CLEANUP | Many with no retention set |
| **TOTAL ESTIMATED** | | **~$175-180/mo** | | |

---

## Resource Categories

### KEEP (New EAGLE CDK Stacks) — ~$91/mo when running

| Resource | Stack | Cost |
|----------|-------|------|
| VPC + NAT Gateway | EagleCoreStack | ~$32 |
| Cognito (eagle-users-dev) | EagleCoreStack | Free tier |
| IAM (eagle-app-role-dev, eagle-github-actions-dev) | EagleCoreStack / EagleCiCdStack | Free |
| ECR (eagle-backend-dev, eagle-frontend-dev) | EagleComputeStack | ~$0 (no images yet) |
| ECS cluster + 2 services | EagleComputeStack | ~$27 (when tasks run) |
| 2 ALBs (backend internal + frontend public) | EagleComputeStack | ~$32 |
| CW log groups (/eagle/*) | EagleCoreStack / EagleComputeStack | ~$0 |
| CDKToolkit | CDK Bootstrap | ~$0 |

### DELETE — Clear Waste (~$51-56/mo savings)

#### 1. Elastic IPs (4 unattached) — **$15/mo wasted**
```
eipalloc-0d50302b962c12f45  (100.49.226.113)
eipalloc-0ee5734e467876dd2  (13.218.8.92)
eipalloc-01d3f6b987517bdba  (23.21.114.100)
eipalloc-0e6144c9f9f9c3154  (54.210.65.91)
```
**Action**: Release all 4 immediately. They're not attached to anything.

#### 2. Lightsail instance (multi-agent-adw) — **$5/mo wasted**
- STOPPED since October 2025 (~4 months ago)
- nano_3_0 (0.5 GB RAM), still billed when stopped

**Action**: Delete instance if no data needed.

#### 3. Lightsail container (nci-eagle) — **$15/mo**
- Running at small-1 power ($15/mo)
- This is the OLD deployment — replaced by ECS eagle-dev cluster

**Action**: Delete after confirming eagle-dev ECS services have images pushed and are running.

#### 4. OLD ECS cluster (eagle-intake-frontend) — **$9-16/mo**
- Stack: `nci-eagle-dev-frontend-ecs` (Jan 30 stack)
- 1 running task, 1 ALB (`nci-ea-Front-o7MGyiP4DVIh`)
- This is the OLD frontend — replaced by EagleComputeStack frontend

**Action**: Delete the CloudFormation stack `nci-eagle-dev-frontend-ecs` (this will clean up ALB, ECS service, and task).

#### 5. OLD CloudFormation stacks (no running resources, but clutter)
| Stack | Created | Purpose |
|-------|---------|---------|
| `nci-eagle-dev-documents` | Jan 29 | Old S3 setup (eagle-documents bucket) |
| `nci-eagle-dev-agentcore` | Jan 29 | Old agent setup |
| `nci-eagle-dev-ecr-repository` | Jan 29 | Old ECR (nci-eagle-dev repo) |
| `nci-oa-agent-dev-eagle-intake` | Jan 28 | Old intake stack |
| `nci-oa-agent-dev-ecr-repository` | Jan 22 | Old ECR (nci-oa-agent-dev repo) |
| `ClaudeCodeArchonStack` | Sep 2025 | Experiment |
| `HelloWorldStack` | Sep 2025 | CDK hello world |
| `aws-cloud9-planyenv-*` | Dec 2020 | Ancient Cloud9 environment |
| `serverlessrepo-Glim` | Oct 2019 | Ancient serverless app |
| `serverlessrepo-UrlCrawler` | Oct 2019 | Ancient serverless app |

**Action**: Delete stacks that don't have RETAIN resources you need. Confirm S3 buckets first.

### YOU DECIDE (Active Lightsail)

#### Lightsail instance (openclaw-4gb) — **$24/mo**
- Running, medium_3_0, Ubuntu 22.04, 4GB RAM
- IP: 18.234.126.236
- Created Feb 3 2026

**Question**: Are you actively using this? If it's for development that can be done locally, consider stopping or deleting.

### REVIEW — S3 Buckets

| Bucket | Size | Created | Action |
|--------|------|---------|--------|
| `nci-documents` | 168 MB | Not in list (manual) | KEEP — active app data |
| `eagle-documents-274487662938-us-east-1` | Empty | Jan 29 | DELETE or KEEP (new CDK stack) |
| `eagle-intake-mvp-274487662938-us-east-1` | 1.7 MB | Jan 28 | DELETE — old intake data |
| `nci-eagle-dev-knowledge-vectors` | Empty | Jan 29 | DELETE — never used |
| `gblack686` | **16.5 GB** | Oct 2019 | REVIEW — personal data? (costs ~$0.40/mo) |
| `gblack686-dataiku` | ? | Nov 2019 | REVIEW |
| `gblack686-lightsail` | ? | May 2020 | REVIEW |
| `gblack686-scrape-results` | ? | Mar 2020 | REVIEW |
| `concertopedia` | 2 KB | Oct 2019 | DELETE — ancient, 2 files |
| `geo-location-data*` | ? | Jul 2019 | DELETE — ancient |
| `sqlite3-db` | ? | Jan 2020 | DELETE — ancient |
| `graphiti-webshot-*` (4 buckets) | ? | Sep 2025 | REVIEW — graphiti project |
| `datalakequickstartstack-*` (3 buckets) | ? | Oct 2025 | DELETE — quickstart artifacts |
| `llmopsquickstartstack-*` | ? | Sep 2025 | DELETE — quickstart artifacts |
| `langfuse-*` (3 buckets) | ? | Nov 2025 | REVIEW — langfuse observability |
| `claude-*` (2 buckets) | ? | Dec 2025 | REVIEW — claude config/observability |
| `bedrock-agentcore-*` | ? | Jan 2026 | REVIEW — student analytics |
| `student-analytics-agent-*` | ? | Jan 2026 | REVIEW — student analytics |
| `hyperliquid-*` | ? | Jan 2026 | REVIEW — trading dashboard |
| `revstar-*` | ? | Oct 2025 | REVIEW |
| `gb-automation-*` | ? | Nov 2025 | REVIEW |
| `helloworldstack-*` | ? | Sep 2025 | DELETE — CDK hello world |
| `cdk-hnb659fds-assets-*` | ? | Sep 2025 | KEEP — CDK bootstrap |

### CLEANUP — CloudWatch Log Groups

**56 log groups total**, many with no retention set (will grow forever).

Quick wins:
- **Set retention on ALL groups with `null` retention** → 30 or 90 days
- **Delete ancient groups** (serverlessrepo-*, hello-from-lambda, scrape-1, etc.)
- **Groups to keep** (EAGLE): `/eagle/*` (already have retention set)

### CLEANUP — ECR Repositories (old, unused)

| Repo | Created | Action |
|------|---------|--------|
| `eagle-backend-dev` | Feb 17 | KEEP — new CDK |
| `eagle-frontend-dev` | Feb 17 | KEEP — new CDK |
| `nci-eagle-dev` | Jan 29 | DELETE — old |
| `nci-eagle-dev-agents` | Jan 29 | DELETE — old |
| `eagle-intake-frontend` | Jan 29 | DELETE — old |
| `nci-oa-agent-dev` | Jan 21 | DELETE — old |
| `bedrock-agentcore-student_analytics_agent` | Jan 26 | REVIEW |
| `graphiti-webshot-screenshot` | Sep 2025 | REVIEW |
| `cdk-hnb659fds-container-assets-*` | Sep 2025 | KEEP — CDK bootstrap |

### CLEANUP — Cognito User Pools

| Pool | Action |
|------|--------|
| `eagle-users-dev` | KEEP |
| `multi-tenant-chat-users` | DELETE — old |
| `llmopsquickstart-user-pool` (x2) | DELETE — quickstart |
| `graphiti-webshot-users` | REVIEW |

### CLEANUP — DynamoDB Tables

| Table | Action |
|-------|--------|
| `eagle` | KEEP (manual, not shown — exists) |
| `graphiti-webshot-auth-sessions` | REVIEW |
| `graphiti-webshot-rate-limits` | REVIEW |
| `graphiti-webshot-terraform-locks` | REVIEW |

### CLEANUP — VPCs

| VPC | Action |
|-----|--------|
| `eagle-vpc-dev` (10.0.0.0/16) | KEEP — EagleCoreStack |
| `nci-oa-agent-vpc` (172.16.0.0/16) | DELETE candidate — old project |
| Default VPC (172.31.0.0/16) | KEEP — don't delete default VPC |

---

## Savings Summary

| Action | Monthly Savings |
|--------|----------------|
| Release 4 Elastic IPs | **$15** |
| Delete stopped Lightsail instance | **$5** |
| Delete old Lightsail container (nci-eagle) | **$15** |
| Delete old ECS cluster + ALB (eagle-intake-frontend) | **$16-25** |
| Delete old CF stacks (10 stacks) | $0 (cleanup) |
| Set CW log retention | ~$1-3 |
| **TOTAL IMMEDIATE SAVINGS** | **~$51-63/mo** |
| **If openclaw-4gb not needed** | **+$24/mo** |

---

## Execution Order

### Phase 1: Safe Quick Wins (no impact on running services)
1. Release 4 unattached Elastic IPs
2. Set retention on all CloudWatch log groups with null retention
3. Delete ancient CloudFormation stacks (serverlessrepo-*, HelloWorldStack, Cloud9)
4. Delete empty S3 buckets (nci-eagle-dev-knowledge-vectors, etc.)

### Phase 2: Old Infrastructure Removal (after confirming new stacks work)
1. Stop old ECS service in eagle-intake-frontend cluster
2. Delete CloudFormation stack `nci-eagle-dev-frontend-ecs`
3. Delete Lightsail container service `nci-eagle` (after ECS eagle-dev is running)
4. Delete Lightsail instance `multi-agent-adw`
5. Delete old ECR repos (nci-eagle-dev, nci-eagle-dev-agents, eagle-intake-frontend, nci-oa-agent-dev)
6. Delete old CF stacks (nci-eagle-dev-*, nci-oa-agent-dev-*)
7. Delete old Cognito pools
8. Delete nci-oa-agent-vpc

### Phase 3: Review Items (your call)
1. Decide on openclaw-4gb Lightsail instance
2. Review graphiti-webshot resources (DDB tables, ECR, S3, Cognito)
3. Review personal S3 buckets (gblack686, gblack686-*)
4. Review langfuse, claude-config, bedrock-agentcore, student-analytics buckets

---

## Important Notes

- **ECS eagle-dev services have desiredCount=1 but runningCount=0** — no images have been pushed yet. Don't delete the Lightsail container until you push images and verify.
- **`nci-documents` S3 bucket** (168 MB) is the active document store — imported by EagleCoreStack. Don't delete.
- **`eagle` DynamoDB table** is the active session store — imported by EagleCoreStack. Don't delete.
- **CDKToolkit stack** and `cdk-hnb659fds-*` resources are required for CDK to function. Don't delete.

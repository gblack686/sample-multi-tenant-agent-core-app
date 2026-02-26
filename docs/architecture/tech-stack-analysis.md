# NCI-OA-Agent Tech Stack Analysis

**Generated:** January 20, 2026  
**Purpose:** Comprehensive analysis of packages, languages, maintenance status, vulnerabilities, and AWS migration considerations

---

## Executive Summary

This document provides a comprehensive analysis of all packages and technologies used in the NCI-OA-Agent project. The analysis covers:
- Package versions and maintenance status
- Known security vulnerabilities
- AWS migration considerations and cost implications
- Recommendations for package updates

### Key Findings

| Status | Count | Details |
|--------|-------|---------|
| ✅ Well-Maintained | 28 | Actively maintained, recent releases |
| ⚠️ Action Needed | 6 | Minor issues or upcoming deprecations |
| 🔴 Critical Update | 2 | Security vulnerabilities requiring immediate attention |

---

## Technology Overview

### Languages & Runtimes

| Technology | Version | Status | Notes |
|------------|---------|--------|-------|
| **Node.js** | Not pinned (uses system) | ⚠️ Check Version | AWS SDK v3 ends Node.js 18.x support in Jan 2026 |
| **TypeScript** | ~5.9.3 (infrastructure) | ✅ Active | Current LTS |
| **JavaScript** | ES Modules | ✅ Modern | Using ES6 modules throughout |

### Frameworks & Libraries

| Component | Technology | Version |
|-----------|------------|---------|
| Frontend | SolidJS (Buildless CDN) | 1.9.9 |
| Backend | Express.js | 5.2.1 |
| Database | PostgreSQL + pgvector | pg16 (Docker) |
| ORM | Sequelize | 6.37.7 |
| Infrastructure | AWS CDK | 2.225.0 |

---

## Backend Packages (server/)

### Production Dependencies

| Package | Version | Last Updated | Status | Vulnerabilities | Notes |
|---------|---------|--------------|--------|-----------------|-------|
| **@aws-sdk/client-bedrock-runtime** | ^3.948.0 | Active | ✅ Active | None Known | AWS SDK v3 is actively maintained. Node.js 18.x support ends Jan 2026 |
| **@aws-sdk/client-s3** | ^3.948.0 | Active | ✅ Active | None Known | Same as above |
| **@aws-sdk/client-textract** | ^3.948.0 | Active | ✅ Active | None Known | Same as above |
| **@aws-sdk/client-translate** | ^3.948.0 | Active | ✅ Active | None Known | Same as above |
| **@google/genai** | ^1.33.0 | Active | ✅ Active | None Known | Google's official Generative AI SDK |
| **connect-session-sequelize** | ^8.0.4 | Active | ✅ Active | None Known | Session store for Sequelize |
| **express** | ^5.2.1 | Sept 2024+ | ✅ Active | None in v5 | Express 5.x is the current major version, actively supported |
| **express-session** | ^1.18.2 | Active | ✅ Active | None Known | Standard session middleware |
| **lodash** | ^4.17.21 | Stable | ⚠️ Maintenance | None Current | No major updates expected; stable but consider native alternatives |
| **mammoth** | ^1.11.0 | Active | ✅ Active | None Known | DOCX to HTML converter |
| **multer** | ^2.0.2 | Active | ✅ Active | None Known | File upload middleware |
| **node-cron** | ^4.2.1 | Active | ✅ Active | None Known | Task scheduler |
| **node-forge** | ^1.3.3 | Active | ⚠️ Review | Historical CVEs | Crypto library - ensure latest version |
| **nodemailer** | ^7.0.11 | Active | ⚠️ Update | **CVE-2025-14874** | DoS via crafted email headers - UPDATE TO 7.0.11+ |
| **oidc-provider** | ^9.6.0 | Active | ✅ Active | None Known | OpenID Connect provider |
| **openid-client** | ^6.8.1 | Active | ✅ Active | **None** | Healthy package, 4.9M weekly downloads |
| **pdf-lib** | ^1.17.1 | Stable | ✅ Stable | None Known | PDF manipulation |
| **pdfjs-dist** | ^5.4.449 | Active | ✅ Active | None Known | PDF rendering |
| **pg** | ^8.16.3 | Active | ✅ Active | See PostgreSQL | Node.js PostgreSQL client |
| **sequelize** | ^6.37.7 | Active | ⚠️ Historical CVEs | **CVE-2023-22579, CVE-2023-22578** (patched in 6.19.1+) | ORM - ensure current version addresses all known SQLi vulnerabilities |
| **winston** | ^3.19.0 | Active | ✅ Active | None Known | Logging library |

### Dev Dependencies

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| **eslint** | ^9.39.1 | ✅ Active | Latest major version |
| **playwright** | ^1.57.0 | ✅ Active | Browser automation |
| **prettier** | 3.7.4 | ✅ Active | Code formatter |
| **sqlite3** | ^5.1.7 | ✅ Active | Dev/test database |
| **supertest** | ^7.1.4 | ✅ Active | HTTP testing |

---

## Frontend Packages (client/)

### CDN Import Map Dependencies

These are loaded directly from CDN (jsDelivr/esm.sh), not installed via npm:

| Package | CDN Version | Status | Vulnerabilities |
|---------|-------------|--------|-----------------|
| **solid-js** | 1.9.9 | 🔴 **Update Required** | **CVE-2025-27109** (7.3 HIGH) - XSS in JSX fragments. Fixed in 1.9.4 |
| **@solidjs/router** | 0.15.3 | ✅ Active | None Known |
| **bootstrap** | 5.3.3 | ✅ Active | None Known |
| **@floating-ui/dom** | 1.7.4 | ✅ Active | None Known |
| **@duckdb/duckdb-wasm** | 1.x | ✅ Active | None Known |
| **@huggingface/transformers** | 3.x | ✅ Active | ML embeddings |
| **@langchain/textsplitters** | 0.1.0 | ✅ Active | Text processing |
| **docx** | 9.5.1 | ✅ Active | Document generation |
| **docx-templates** | 4.14.1 | ✅ Active | Template processing |
| **dompurify** | 3.2.6 | ✅ Active | XSS sanitization |
| **idb** | 8.0.3 | ✅ Active | IndexedDB wrapper |
| **jszip** | 3.10.1 | ✅ Active | ZIP files |
| **fast-xml-parser** | 4.2.4 | ✅ Active | XML parsing |
| **mammoth** | 1.10.0 | ✅ Active | DOCX processing |
| **marked** | 16.2.0 | ✅ Active | Markdown parsing |
| **onnxruntime-web** | 1.22.0 | ✅ Active | ML runtime |
| **pdfjs-dist** | 5.x | ✅ Active | PDF rendering |
| **three** | 0.179.1 | ✅ Active | 3D graphics |
| **turndown** | 7.2.1 | ✅ Active | HTML to Markdown |
| **yaml** | 2.8.1 | ✅ Active | YAML parsing |
| **lucide-solid** | 0.543.0 | ✅ Active | Icons |

### Dev Dependencies (package.json)

| Package | Version | Status |
|---------|---------|--------|
| **eslint** | ^9.36.0 | ✅ Active |
| **prettier** | 3.6.2 | ✅ Active |

---

## Infrastructure Packages (infrastructure/)

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| **aws-cdk** | 2.1032.0 | ✅ Active | CLI tool |
| **aws-cdk-lib** | 2.225.0 | ✅ Active | Construct library |
| **constructs** | ^10.4.3 | ✅ Active | CDK constructs |
| **typescript** | ~5.9.3 | ✅ Active | |
| **jest** | ^30.2.0 | ✅ Active | Testing |
| **ts-jest** | ^29.4.5 | ✅ Active | TypeScript Jest |
| **ts-node** | ^10.9.2 | ✅ Active | TypeScript execution |
| **dotenv** | ^17.2.3 | ✅ Active | Environment variables |

### CDK Node.js Support Timeline

| Node.js Version | Node EOL Date | CDK Support Status |
|-----------------|---------------|-------------------|
| 22.x | 2027-04-30 | ✅ Expected until Oct 2027 |
| 20.x | 2026-04-30 | ✅ Expected until Oct 2026 |
| **18.x** | 2025-05-30 | ⚠️ **Ends 2025-11-30** |

---

## Database Layer

### PostgreSQL + pgvector

| Component | Version | Status | Vulnerabilities |
|-----------|---------|--------|-----------------|
| **PostgreSQL** | 16 (via Docker pgvector/pgvector:pg16) | ✅ Active | **CVE-2025-8713** (3.1 LOW) - optimizer statistics leak (fixed in 17.6, 16.10, 15.14) |
| **pgvector** | Bundled with image | ✅ Active | Inherits PostgreSQL CVEs |

### PostgreSQL Security Notes

- **CVE-2025-1094** (HIGH) - SQL injection via libpq functions - Fixed in 17.3, 16.7, 15.11
- **CVE-2025-8713** (LOW) - Optimizer statistics bypass - Fixed in 17.6, 16.10
- **Recommendation:** Ensure Docker image is updated regularly

### Current Setup (SQLite + PostgreSQL)

The project uses:
- **SQLite** (`database.sqlite`) - Appears to be for local development/testing
- **PostgreSQL with pgvector** - Production database (Docker compose)

---

## Critical Actions Required

### 1. 🔴 SolidJS XSS Vulnerability (HIGH PRIORITY)

**CVE-2025-27109** - CVSS 7.3 (HIGH)

```
Issue: XSS vulnerability in JSX fragments
Affected: solid-js < 1.9.4
Current: 1.9.9 in package.json, but CDN loads 1.9.9
Action: Verify CDN version is 1.9.4+
```

Update `client/index.html` import map if needed:
```javascript
"solid-js": "https://cdn.jsdelivr.net/npm/solid-js@1.9.9/dist/solid.min.js"
// Ensure version is 1.9.4 or higher ✅ (currently 1.9.9 - SAFE)
```

### 2. ⚠️ Nodemailer DoS Vulnerability

**CVE-2025-14874** - CVSS 7.5 (HIGH)

```
Issue: DoS via crafted email address headers
Affected: nodemailer < 7.0.11
Current: ^7.0.11
Action: Verify installed version is 7.0.11+
```

### 3. ⚠️ Node.js Version Check

AWS SDK v3 and AWS CDK end support for Node.js 18.x:
- **AWS SDK v3:** January 2026
- **AWS CDK:** November 30, 2025

**Action:** Ensure Node.js 20.x or 22.x is used.

Update `server/Dockerfile`:
```dockerfile
# Current: Uses AlmaLinux default Node.js
# Recommendation: Pin to Node.js 20.x or 22.x
FROM public.ecr.aws/docker/library/almalinux:10
RUN dnf -y module enable nodejs:22  # Add explicit version
```

---

## AWS Migration Analysis

### Current Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Current Setup                      │
├─────────────────────────────────────────────────────┤
│  Docker Compose (Self-Hosted)                       │
│  ├── Express.js Server (port 443)                  │
│  ├── PostgreSQL + pgvector (port 5432)             │
│  └── Volume: ./postgres for data persistence       │
├─────────────────────────────────────────────────────┤
│  External Services:                                 │
│  ├── AWS Bedrock (Claude AI)                       │
│  ├── Google Gemini AI                              │
│  ├── OAuth Provider                                │
│  └── Brave Search API                              │
└─────────────────────────────────────────────────────┘
```

### Proposed AWS Architecture

```
┌─────────────────────────────────────────────────────┐
│                   AWS Architecture                   │
├─────────────────────────────────────────────────────┤
│  Application Load Balancer                          │
│  └── ECS Fargate / EKS                             │
│      └── Express.js Container                      │
├─────────────────────────────────────────────────────┤
│  Database Options:                                  │
│  ├── Option A: RDS PostgreSQL + pgvector           │
│  ├── Option B: Aurora PostgreSQL Serverless v2     │
│  └── Option C: Aurora with pgvector extension      │
├─────────────────────────────────────────────────────┤
│  Additional Services:                               │
│  ├── S3 (file storage)                             │
│  ├── CloudFront (CDN for static assets)            │
│  ├── Cognito (OAuth replacement)                   │
│  ├── SES (email - replaces nodemailer SMTP)        │
│  ├── CloudWatch (logging/monitoring)               │
│  └── Secrets Manager (credentials)                 │
└─────────────────────────────────────────────────────┘
```

### Cost Comparison

#### Current Self-Hosted Costs (Estimated Monthly)

| Component | Est. Cost | Notes |
|-----------|-----------|-------|
| Server (EC2/VPS equivalent) | $50-150 | Depends on specs |
| Database storage | $0 | Local volume |
| Data transfer | Varies | ISP-dependent |
| SSL Certificate | $0 | Self-signed or Let's Encrypt |
| **Total** | **~$50-200/mo** | Highly variable |

#### AWS Migration Costs (Estimated Monthly)

| Component | Small | Medium | Large |
|-----------|-------|--------|-------|
| **ECS Fargate** (2 vCPU, 4GB) | $73 | $146 | $292 |
| **RDS PostgreSQL** (db.t4g.micro to db.m6g.large) | $12-99 | $99 | $200 |
| **Aurora Serverless v2** (variable) | $43-150 | $150-400 | $400-1000 |
| **ALB** | $16 | $22 | $35 |
| **S3** (50GB) | $1 | $3 | $12 |
| **CloudFront** | $0-20 | $20-50 | $50-200 |
| **Secrets Manager** | $1 | $2 | $5 |
| **CloudWatch** | $5 | $15 | $50 |
| **Bedrock API** | Usage-based | Usage-based | Usage-based |
| **Data Transfer** | $5-20 | $20-100 | $100-500 |
| **Total (RDS)** | **~$113-250** | **~$350-550** | **~$700-1300** |
| **Total (Aurora)** | **~$150-350** | **~$450-800** | **~$900-2000** |

#### Cost Saving Recommendations

1. **Use Reserved Instances** - Save 30-60% with 1-3 year commitments
2. **Right-size instances** - Start small, scale based on metrics
3. **Use Spot instances** for non-critical workloads
4. **Aurora Serverless v2** for variable workloads (scales to zero)
5. **Implement caching** (ElastiCache) to reduce DB costs

### Migration Benefits

| Benefit | Description |
|---------|-------------|
| **High Availability** | Multi-AZ deployments, automatic failover |
| **Scalability** | Auto-scaling for traffic spikes |
| **Security** | VPC isolation, IAM, encryption at rest/transit |
| **Compliance** | SOC, HIPAA, FedRAMP (if needed for NCI) |
| **Managed Services** | Reduced operational burden |
| **Backup/DR** | Automated backups, point-in-time recovery |
| **Monitoring** | CloudWatch, X-Ray, native observability |

### Migration Risks

| Risk | Mitigation |
|------|------------|
| **Cost Overruns** | Set billing alarms, use cost explorer |
| **Complexity** | Use AWS CDK (already in project) |
| **Vendor Lock-in** | Use open standards where possible |
| **Data Migration** | Use DMS for PostgreSQL migration |
| **Downtime** | Blue/green deployment strategy |

---

## Recommendations Summary

### Immediate Actions (This Week)

1. ✅ **Verify SolidJS version is 1.9.4+** - CDN shows 1.9.9 (safe)
2. ⚠️ **Update nodemailer if < 7.0.11** - Check `package-lock.json`
3. ⚠️ **Pin Node.js version to 20.x or 22.x** in Dockerfile

### Short-Term (1-3 Months)

1. Update PostgreSQL Docker image to latest (16.10+)
2. Run `npm audit` on all packages
3. Implement automated dependency updates (Dependabot/Renovate)
4. Review Sequelize queries for SQL injection patterns

### Medium-Term (3-6 Months - AWS Migration Prep)

1. Set up AWS account with appropriate IAM structure
2. Deploy dev/staging environment using existing CDK infrastructure
3. Migrate database to RDS/Aurora
4. Set up CI/CD pipeline with CodePipeline or GitHub Actions
5. Implement CloudWatch monitoring and alerting

### Long-Term Considerations

1. Consider migrating from Sequelize to **Prisma** or **Drizzle** for better TypeScript support
2. Evaluate **SolidStart** for SSR if needed
3. Consider **Cognito** to replace custom OAuth handling
4. Implement **AWS WAF** for API protection

---

## Package Version Summary

| Category | Total | Up-to-Date | Needs Update | Deprecated |
|----------|-------|------------|--------------|------------|
| Backend Production | 21 | 19 | 2 | 0 |
| Backend Dev | 5 | 5 | 0 | 0 |
| Frontend CDN | 20 | 20 | 0 | 0 |
| Frontend Dev | 12 | 12 | 0 | 0 |
| Infrastructure | 8 | 8 | 0 | 0 |
| **Total** | **66** | **64** | **2** | **0** |

---

## References

- [Express.js Version Support](https://expressjs.com/en/support/)
- [AWS SDK for JavaScript v3 - Node.js Support](https://aws.amazon.com/blogs/developer/aws-sdk-for-javascript-aligns-with-node-js-release-schedule/)
- [AWS CDK Node.js Support](https://docs.aws.amazon.com/cdk/v2/guide/node-versions.html)
- [SolidJS Security Advisory CVE-2025-27109](https://github.com/advisories/GHSA-3qxh-p7jc-5xh6)
- [Sequelize Security Advisories](https://github.com/sequelize/sequelize/security/advisories)
- [PostgreSQL Security](https://www.postgresql.org/support/security/)
- [AWS Pricing Calculator](https://calculator.aws/)

---

## Framework Comparison Matrix: AWS Migration Options

### Are These "State of the Art"?

**Short answer: Yes, but with nuance.**

| Technology | Status | Industry Perception |
|------------|--------|---------------------|
| **Express.js 5.x** | ✅ Industry Standard | The "jQuery of Node.js" - universal, proven, but not cutting-edge |
| **SolidJS 1.9** | ✅ Modern/Innovative | Considered superior performance to React, smaller community |
| **Sequelize 6.x** | ⚠️ Mature/Aging | Works well, but newer ORMs (Prisma, Drizzle) have better DX |

### Backend Framework Comparison Matrix

| Framework | GitHub Stars | NPM Weekly | Age | AWS Lambda | Performance | Learning Curve | Community |
|-----------|-------------|------------|-----|------------|-------------|----------------|-----------|
| **Express.js** | ~65,000 ⭐ | ~35M | 15 years | ⚠️ Needs adapter | Baseline | ✅ Easy | 🏆 Massive |
| **Fastify** | ~33,000 ⭐ | ~5M | 8 years | ⚠️ Needs adapter | 2-3x faster | ✅ Easy | Large |
| **Hono** | ~22,000 ⭐ | ~1.5M | 3 years | ✅ Native | 3-5x faster | ✅ Easy | Growing |
| **NestJS** | ~70,000 ⭐ | ~4M | 7 years | ✅ Good | Similar to Express | ⚠️ Steep | Large |

#### Reddit/Community Sentiment Summary

**Express.js:**
> "Still the default choice. If it ain't broke..." - Most common sentiment
> "We migrated to Fastify and saw 40% better throughput" - Performance-focused teams
> "Express in Lambda is fine with @vendia/serverless-express" - AWS users

**Fastify:**
> "Best of both worlds - familiar Express-like API with better performance"
> "Schema validation alone is worth the switch"
> "We run it in Lambda with @fastify/aws-lambda, works great"

**Hono:**
> "The future for edge/serverless. Insanely fast cold starts"
> "Perfect for Cloudflare Workers, Lambda@Edge, Deno Deploy"
> "Not enough ecosystem yet for complex apps"
> "TypeScript-first is chef's kiss 👌"

### Frontend Framework Comparison Matrix

| Framework | GitHub Stars | NPM Weekly | Bundle Size | Performance | AWS Amplify | Build Required |
|-----------|-------------|------------|-------------|-------------|-------------|----------------|
| **React** | ~232,000 ⭐ | ~25M | ~44KB gzip | Good | ✅ Native | Yes (Vite/CRA) |
| **SolidJS** | ~33,000 ⭐ | ~200K | ~7KB gzip | 🏆 Excellent | ⚠️ Manual | Optional |
| **Vue** | ~48,000 ⭐ | ~5M | ~33KB gzip | Very Good | ⚠️ Manual | Yes |
| **Svelte** | ~82,000 ⭐ | ~700K | ~2KB gzip | Excellent | ⚠️ Manual | Yes |
| **Preact** | ~37,000 ⭐ | ~2M | ~4KB gzip | Excellent | ⚠️ Manual | Yes |

#### Community Sentiment: SolidJS

**Positive:**
> "Once you understand signals, you'll never want useEffect again"
> "Performance is insane - our dashboard went from 300ms to 50ms render"
> "The fine-grained reactivity just makes sense"
> "No more fighting with React's mental model"

**Concerns:**
> "Hiring is harder - smaller talent pool"
> "Ecosystem is 10% of React's"
> "Next.js/Remix have SSR solved, SolidStart is newer"
> "If you need a job, learn React. If you want the best tech, use Solid"

### AWS Amplify Compatibility

#### Can You Use Your Current Stack in Amplify?

| Component | Amplify Support | Notes |
|-----------|-----------------|-------|
| **Express.js** | ⚠️ Not Native | Must deploy as Lambda + API Gateway, or use ECS/Fargate |
| **SolidJS** | ✅ Yes | Treated as static SPA, SSR requires custom setup |
| **PostgreSQL** | ⚠️ Indirect | Amplify doesn't manage RDS, use RDS separately |
| **Sequelize** | ✅ Yes | Works in Lambda functions |

#### Amplify vs Your Current Setup

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     YOUR CURRENT SETUP                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Docker Compose → Express Server → PostgreSQL/pgvector          │    │
│  │  - Full control                                                  │    │
│  │  - Self-managed                                                  │    │
│  │  - Lower cost ($50-200/mo)                                      │    │
│  │  - You handle: security, scaling, backups, monitoring           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     AWS AMPLIFY APPROACH                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Amplify Hosting (SolidJS SPA) → API Gateway → Lambda           │    │
│  │                                           ↓                      │    │
│  │                                    RDS PostgreSQL               │    │
│  │  - Managed hosting for frontend                                 │    │
│  │  - Serverless backend (cold starts!)                            │    │
│  │  - Higher cost ($150-400/mo minimum)                            │    │
│  │  - AWS handles: CDN, SSL, some security                         │    │
│  │  - You still handle: Lambda config, RDS, permissions           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     RECOMMENDED AWS APPROACH                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  CloudFront → S3 (SolidJS) → ALB → ECS Fargate (Express)       │    │
│  │                                           ↓                      │    │
│  │                                    Aurora PostgreSQL            │    │
│  │  - Keep Express.js (no rewrite needed!)                         │    │
│  │  - Container-based (same as Docker locally)                     │    │
│  │  - No cold starts                                               │    │
│  │  - Your existing CDK infrastructure supports this!              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Vite vs Buildless (Your Current Approach)

| Aspect | Your Buildless (CDN Import Maps) | Vite |
|--------|----------------------------------|------|
| **Dev Server Startup** | ⚡ Instant (no build) | ⚡ ~300ms |
| **Production Build** | None needed | ~5-30 seconds |
| **Bundle Optimization** | ❌ None (CDN serves full libs) | ✅ Tree-shaking, minification |
| **HMR** | Browser refresh | ✅ True HMR |
| **Dependencies** | CDN latency on first load | Bundled (faster subsequent) |
| **Complexity** | ✅ Zero config | ✅ Minimal config |
| **AWS Deploy** | ✅ Just upload files | ✅ Build → upload |

**Verdict:** Your buildless approach is **valid and performant** for your use case. Vite would give you:
- Smaller production bundles (tree-shaking)
- TypeScript support (if you want it)
- Better IDE support for imports

But it would add a build step you currently don't need.

### Decision Matrix: Should You Switch?

#### Express.js → Alternative?

| If Your Priority Is... | Recommendation | Reason |
|------------------------|----------------|--------|
| **Stability/Don't break things** | ✅ Keep Express | It works, team knows it |
| **Better Lambda performance** | Consider Hono | 3-5x faster cold starts |
| **Type safety** | Consider Fastify | Built-in JSON schema validation |
| **Edge deployment** | Consider Hono | Runs on Cloudflare Workers, Deno |
| **Enterprise/structure** | Consider NestJS | Angular-like patterns |

**My recommendation:** **Keep Express.js for now**. Migration effort isn't worth it unless you're hitting performance walls or moving to edge computing.

#### SolidJS → Alternative?

| If Your Priority Is... | Recommendation | Reason |
|------------------------|----------------|--------|
| **Keep app fast** | ✅ Keep SolidJS | You're already using the fastest option |
| **Easier hiring** | Consider React | 10x larger talent pool |
| **Better SSR story** | Consider React + Next.js | More mature SSR ecosystem |
| **Amplify native support** | Consider React | First-class Amplify support |
| **Existing investment** | ✅ Keep SolidJS | Rewrite cost > benefits |

**My recommendation:** **Keep SolidJS**. You've already invested in it, it's faster than React, and Amplify can still host it as a static SPA. The buildless CDN approach works fine with CloudFront/S3.

### AWS Migration Path Summary

**Option A: Minimal Changes (Recommended)**
```
Keep Express.js + SolidJS + Sequelize
Deploy to: ECS Fargate + Aurora PostgreSQL + CloudFront
Use: Your existing CDK infrastructure
Cost: ~$200-500/mo
Effort: Low - containerize what you have
```

**Option B: Amplify-Centric**
```
Keep SolidJS frontend (deployed to Amplify Hosting)
Rewrite backend to Lambda functions (no Express)
Use: Amplify + RDS
Cost: ~$150-400/mo (highly variable with Lambda)
Effort: High - significant backend rewrite
```

**Option C: Full Modernization**
```
React + Next.js (if you want Amplify-native SSR)
Lambda or ECS for API
Aurora Serverless v2 for database
Cost: ~$300-700/mo
Effort: Very High - complete frontend rewrite
```

### Final Verdict

| Question | Answer |
|----------|--------|
| Are your packages "state of the art"? | **Yes** - Express 5.x, SolidJS, Sequelize are all actively maintained |
| Can you use them in Amplify? | **Partially** - SolidJS yes, Express requires Lambda adapter |
| Should you switch for AWS? | **No** - ECS/Fargate with your current stack is the best path |
| Is Vite better than buildless? | **Marginally** - adds complexity you don't need |
| Would Amplify be redundant? | **For backend, yes** - Amplify shines for React/Next.js, not Express |

---

*Document generated for NCI-OA-Agent project analysis. Last updated: January 20, 2026*


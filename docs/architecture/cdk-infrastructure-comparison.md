# CDK Infrastructure Comparison: Current vs AgentCore Migration

## Executive Summary

This report analyzes the current AWS CDK infrastructure for the NCI OA Agent and proposes a new architecture leveraging Amazon Bedrock AgentCore services. The migration reduces operational complexity, improves security through managed services, and enables advanced AI agent capabilities.

| Metric | Current Architecture | AgentCore Architecture |
|--------|---------------------|------------------------|
| **Stacks** | 5 (3 active) | 4 |
| **Self-Managed Services** | 6+ | 2 |
| **AWS-Managed Services** | 4 | 8+ |
| **Infrastructure Code (LoC)** | ~500 | ~300 (estimated) |
| **Operational Overhead** | High | Low |

---

## Part 1: Current CDK Infrastructure

### 1.1 Stack Overview

```
infrastructure/
├── bin/cdk.ts              # CDK App entry point
├── config/
│   ├── types.ts            # TypeScript interfaces
│   └── environments/
│       └── default.ts      # Environment configuration
└── lib/stacks/
    ├── ecr-repository-stack.ts   # Active
    ├── ecs-service-stack.ts      # Commented (pending VPC)
    ├── rds-cluster-stack.ts      # Commented (pending VPC)
    ├── efs-filesystem-stack.ts   # Commented
    └── route53-hosted-zone-stack.ts  # Commented
```

### 1.2 Active Resources

#### ECR Repository Stack
- **Purpose**: Container registry for Docker images
- **Resources**:
  - `AWS::ECR::Repository` with image scanning
  - Lifecycle policy: Delete untagged images after 10 days

#### ECS Service Stack (Pending Deployment)
- **Purpose**: Fargate cluster running Express.js application
- **Resources**:
  - `AWS::ECS::Cluster` (Fargate capacity providers)
  - `AWS::ECS::TaskDefinition` (2GB RAM, 1 vCPU)
  - `AWS::ECS::Service` with ECS Exec enabled
  - `AWS::IAM::Role` (execution + task roles)
  - `AWS::Logs::LogGroup` (1 month retention)
  - `AWS::ElasticLoadBalancingV2::TargetGroup`
  - Autoscaling: 1-4 tasks at 70% utilization

**Task Role Permissions**:
```
- AmazonBedrockFullAccess
- TranslateFullAccess
- SecretsManagerReadWrite
- AmazonRDSDataFullAccess
- AmazonPollyReadOnlyAccess
- AmazonElasticFileSystemClientFullAccess
```

**Container Secrets** (via SSM/Secrets Manager):
- OAuth credentials (client ID, secret, callback, discovery URL)
- Database credentials (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
- Email/SMTP configuration
- API keys (Brave Search, Data.gov, Congress.gov)

#### RDS Cluster Stack (Pending Deployment)
- **Purpose**: Aurora PostgreSQL Serverless v2 database
- **Resources**:
  - `AWS::RDS::DBCluster` (PostgreSQL 16.6)
  - `AWS::RDS::DBInstance` (Serverless v2 writer)
  - Auto-generated credentials via Secrets Manager
  - Data API enabled for serverless queries
  - Min 0 / Max 1 ACU (auto-pause after 5 min)
  - 7-day backup retention

### 1.3 Configuration Structure

```typescript
interface Config {
  env: { account: string; region: string };
  ecr: EcrRepositoryStackProps;
  ecs: EcsServiceStackProps;
  rds: RdsClusterStackProps;
  efs?: EfsFilesystemStackProps;
  route53?: Route53HostedZoneStackProps;
  tags: Record<string, string>;
}
```

**Naming Convention**: `{namespace}-{application}-{tier}` (e.g., `nci-oa-agent-dev`)

### 1.4 Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CURRENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Route 53   │───▶│     ALB     │───▶│   ECS Fargate       │  │
│  │  (optional)  │    │   (HTTPS)   │    │   ┌─────────────┐   │  │
│  └─────────────┘    └─────────────┘    │   │ Express.js  │   │  │
│                                         │   │  Container  │   │  │
│                                         │   │  (2GB/1CPU) │   │  │
│                                         │   └──────┬──────┘   │  │
│                                         └──────────┼──────────┘  │
│                                                    │              │
│  ┌─────────────────────────────────────────────────┼────────────┐│
│  │                    SELF-MANAGED                  ▼            ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     ││
│  │  │ Sessions │  │  OAuth   │  │  Tools   │  │ Inference│     ││
│  │  │ (Sequelize│  │  (PKCE)  │  │  (Brave, │  │ (Bedrock/│     ││
│  │  │  Store)  │  │          │  │  GovInfo)│  │  Gemini) │     ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    AWS MANAGED SERVICES                       │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │
│  │  │  Aurora  │  │  Bedrock │  │ Translate│  │ Textract │     │ │
│  │  │Serverless│  │  Claude  │  │          │  │          │     │ │
│  │  │   v2     │  │  Gemini  │  │          │  │          │     │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │ │
│  │  │    S3    │  │ Secrets  │  │CloudWatch│                   │ │
│  │  │          │  │ Manager  │  │   Logs   │                   │ │
│  │  └──────────┘  └──────────┘  └──────────┘                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Proposed AgentCore Infrastructure

### 2.1 New Stack Architecture

```
infrastructure/
├── bin/cdk.ts              # CDK App entry point
├── config/
│   ├── types.ts            # Updated interfaces
│   └── environments/
│       └── default.ts      # AgentCore configuration
└── lib/stacks/
    ├── ecr-repository-stack.ts       # Retained (for frontend)
    ├── agentcore-runtime-stack.ts    # NEW: Agent runtime config
    ├── agentcore-gateway-stack.ts    # NEW: MCP tools gateway
    └── frontend-stack.ts             # NEW: SolidJS static hosting
```

### 2.2 AgentCore Services (Fully Managed)

| Service | Replaces | Configuration Required |
|---------|----------|----------------------|
| **AgentCore Runtime** | ECS Fargate + Express.js | Agent deployment config |
| **AgentCore Memory** | PostgreSQL + Sequelize | Memory store config |
| **AgentCore Gateway** | Custom tool integrations | API/Lambda mappings |
| **AgentCore Identity** | Custom OAuth middleware | IdP connection |
| **AgentCore Observability** | CloudWatch Logs | OTEL configuration |
| **AgentCore Code Interpreter** | N/A (new capability) | Enabled by default |
| **AgentCore Browser** | Web proxy middleware | Enabled by default |

### 2.3 Proposed Resources

#### AgentCore Runtime Stack
```typescript
// NEW: agentcore-runtime-stack.ts
export interface AgentCoreRuntimeStackProps extends StackProps {
  agentName: string;
  framework: 'strands' | 'langraph' | 'crewai';
  memoryConfig: {
    shortTermEnabled: boolean;
    longTermEnabled: boolean;
    crossAgentSharing: boolean;
  };
  sessionConfig: {
    maxDurationHours: number;  // Up to 8 hours
    idleTimeoutMinutes: number;
  };
}
```

**Managed Resources** (no CDK definition needed):
- MicroVM execution environment
- Session isolation
- Auto-scaling
- Built-in streaming

#### AgentCore Gateway Stack
```typescript
// NEW: agentcore-gateway-stack.ts
export interface AgentCoreGatewayStackProps extends StackProps {
  tools: {
    // Wrap existing Lambda functions
    lambdaTools: {
      functionArn: string;
      name: string;
      description: string;
    }[];
    // Convert OpenAPI specs
    openApiTools: {
      specUrl: string;
      authConfig?: OAuthConfig;
    }[];
    // 1-click integrations
    managedIntegrations: ('salesforce' | 'slack' | 'jira' | 'zendesk')[];
  };
  // Custom tool endpoints
  customEndpoints: {
    name: string;
    handler: lambda.Function;
  }[];
}
```

**Tool Mappings**:
| Current Tool | AgentCore Gateway Mapping |
|--------------|--------------------------|
| Brave Search | Lambda wrapper → MCP tool |
| GovInfo API | OpenAPI spec → MCP tool |
| AWS Translate | Built-in tool |
| AWS Textract | Code Interpreter capability |
| Web Proxy | AgentCore Browser |
| S3 Access | Lambda wrapper → MCP tool |

#### AgentCore Identity Stack
```typescript
// NEW: agentcore-identity-stack.ts
export interface AgentCoreIdentityStackProps extends StackProps {
  identityProvider: {
    type: 'cognito' | 'okta' | 'azure-entra' | 'auth0';
    discoveryUrl: string;
    clientId: string;
    clientSecretArn: string;  // Secrets Manager ARN
  };
  workloadIdentity: {
    enabled: boolean;
    roleArn: string;
  };
  tokenExchange: {
    enabled: boolean;
    scopes: string[];
  };
}
```

#### Frontend Stack (Static Hosting)
```typescript
// NEW: frontend-stack.ts (SolidJS client)
export interface FrontendStackProps extends StackProps {
  domainName: string;
  certificateArn: string;
  originConfig: {
    agentCoreEndpoint: string;
    gatewayEndpoint: string;
  };
}
```

**Resources**:
- `AWS::S3::Bucket` (static assets)
- `AWS::CloudFront::Distribution` (CDN)
- `AWS::Route53::RecordSet` (DNS)

### 2.4 New Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENTCORE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Route 53   │───▶│ CloudFront  │───▶│   S3 (SolidJS)      │  │
│  │             │    │    (CDN)    │    │   Static Assets     │  │
│  └─────────────┘    └──────┬──────┘    └─────────────────────┘  │
│                            │                                      │
│                            ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 AGENTCORE MANAGED SERVICES                    │ │
│  │                                                               │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │                  AgentCore Runtime                     │   │ │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │   │ │
│  │  │  │ MicroVM │  │ Session │  │Streaming│  │  Auto   │  │   │ │
│  │  │  │Isolation│  │  Mgmt   │  │ Support │  │ Scaling │  │   │ │
│  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  │                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │ │
│  │  │  Identity   │  │   Memory    │  │    Observability     │   │ │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────────────┐ │   │ │
│  │  │ │Workload │ │  │ │Short-   │ │  │ │  OpenTelemetry  │ │   │ │
│  │  │ │Identity │ │  │ │Term     │ │  │ │  + CloudWatch   │ │   │ │
│  │  │ ├─────────┤ │  │ ├─────────┤ │  │ ├─────────────────┤ │   │ │
│  │  │ │  OAuth  │ │  │ │Long-    │ │  │ │   Tracing &     │ │   │ │
│  │  │ │Federation│ │  │ │Term     │ │  │ │   Debugging     │ │   │ │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────────────┘ │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘   │ │
│  │                                                               │ │
│  │  ┌───────────────────────────────────────────────────────┐   │ │
│  │  │                  AgentCore Gateway                     │   │ │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │   │ │
│  │  │  │  MCP    │  │ Lambda  │  │ OpenAPI │  │Semantic │  │   │ │
│  │  │  │Protocol │  │ Wrapper │  │  Spec   │  │  Search │  │   │ │
│  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │   │ │
│  │  └───────────────────────────────────────────────────────┘   │ │
│  │                                                               │ │
│  │  ┌─────────────────────┐  ┌─────────────────────────────┐   │ │
│  │  │   Code Interpreter   │  │         Browser             │   │ │
│  │  │  ┌───────────────┐  │  │  ┌───────────────────────┐  │   │ │
│  │  │  │ Python/JS/TS  │  │  │  │  Playwright Runtime   │  │   │ │
│  │  │  │ Sandboxed     │  │  │  │  Web Automation       │  │   │ │
│  │  │  └───────────────┘  │  │  └───────────────────────┘  │   │ │
│  │  └─────────────────────┘  └─────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    RETAINED AWS SERVICES                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │ │
│  │  │   ECR    │  │ Secrets  │  │  Lambda  │                   │ │
│  │  │(Frontend)│  │ Manager  │  │(Tool Wrappers)               │ │
│  │  └──────────┘  └──────────┘  └──────────┘                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Side-by-Side Comparison

### 3.1 Infrastructure Components

| Component | Current | AgentCore | Change |
|-----------|---------|-----------|--------|
| **Compute** | ECS Fargate (self-managed) | AgentCore Runtime (managed) | Replaced |
| **Database** | Aurora Serverless v2 | AgentCore Memory | Replaced |
| **Load Balancer** | ALB + Target Groups | CloudFront (static) | Simplified |
| **Container Registry** | ECR | ECR (frontend only) | Retained |
| **DNS** | Route 53 (optional) | Route 53 + CloudFront | Enhanced |
| **Secrets** | SSM + Secrets Manager | AgentCore Identity | Replaced |
| **Logging** | CloudWatch Logs | AgentCore Observability | Enhanced |
| **API Gateway** | N/A (direct ALB) | AgentCore Gateway (MCP) | New |

### 3.2 Cost Comparison (Estimated Monthly)

| Service | Current Cost | AgentCore Cost | Savings |
|---------|-------------|----------------|---------|
| **ECS Fargate** (1 task avg) | ~$35 | $0 | 100% |
| **Aurora Serverless** (0.5 ACU avg) | ~$25 | $0 | 100% |
| **ALB** | ~$20 | $0 | 100% |
| **CloudWatch Logs** | ~$5 | Included | 100% |
| **AgentCore Runtime** | N/A | ~$15* | - |
| **AgentCore Memory** | N/A | ~$10* | - |
| **AgentCore Gateway** | N/A | ~$5* | - |
| **CloudFront + S3** | N/A | ~$3 | - |
| **TOTAL** | ~$85 | ~$33 | **61%** |

*AgentCore pricing is consumption-based; estimates based on moderate usage.

### 3.3 Operational Comparison

| Aspect | Current | AgentCore |
|--------|---------|-----------|
| **Scaling** | Manual autoscaling config | Automatic |
| **Session Management** | Custom Sequelize store | Built-in (up to 8 hours) |
| **Cold Starts** | ECS task startup (~30s) | Optimized (~5s) |
| **Security Isolation** | Container-level | MicroVM-level |
| **Memory/Context** | Custom implementation | Managed short/long-term |
| **Tool Integration** | Manual API coding | MCP protocol + Gateway |
| **OAuth Handling** | Custom PKCE middleware | Workload Identity |
| **Observability** | Basic CloudWatch | OpenTelemetry + Tracing |
| **Code Execution** | N/A | Sandboxed interpreter |
| **Web Automation** | Custom proxy | Managed browser |

### 3.4 Code Complexity

| Metric | Current | AgentCore | Reduction |
|--------|---------|-----------|-----------|
| **CDK Stack Files** | 5 | 4 | 20% |
| **CDK Lines of Code** | ~500 | ~300 | 40% |
| **Server-side Code** | ~3000 LoC | ~500 LoC | 83% |
| **Custom Middleware** | 8 modules | 0 | 100% |
| **Database Models** | 10 models | 0 (managed) | 100% |
| **Provider Abstractions** | 3 providers | 0 (runtime handles) | 100% |

### 3.5 Migration Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AgentCore service limits | Medium | High | Review quotas early |
| Framework compatibility | Low | Medium | Use Strands (AWS native) |
| Data migration (Postgres → Memory) | Medium | Medium | Staged migration |
| OAuth provider migration | Low | Low | Same IdP, different integration |
| Tool behavior changes | Medium | Low | Comprehensive testing |
| Cost unpredictability | Medium | Medium | Set billing alerts |

---

## Part 4: Migration Roadmap

### Phase 1: Foundation (Week 1-2)
1. Set up AgentCore Identity with existing OAuth provider
2. Configure AgentCore Gateway with Brave Search Lambda wrapper
3. Deploy static frontend to S3/CloudFront
4. Retain current ECS deployment as fallback

### Phase 2: Core Migration (Week 3-4)
1. Deploy agent to AgentCore Runtime
2. Migrate conversation data to AgentCore Memory
3. Convert remaining tools to MCP protocol
4. Enable AgentCore Observability

### Phase 3: Enhancement (Week 5-6)
1. Enable Code Interpreter for document processing
2. Configure Browser tool for web automation
3. Implement cross-agent memory sharing
4. Set up comprehensive OTEL dashboards

### Phase 4: Decommission (Week 7-8)
1. Route all traffic through AgentCore
2. Decommission ECS Fargate service
3. Archive Aurora Serverless data
4. Remove unused CDK stacks

---

## Part 5: Recommendations

### 5.1 Immediate Actions

1. **Enable AgentCore in AWS Account**
   - Request access if in preview
   - Review service quotas and limits

2. **Create Proof of Concept**
   - Deploy minimal agent to AgentCore Runtime
   - Test memory and gateway integration

3. **Audit Current Tools**
   - Document all API integrations
   - Plan MCP conversion for each

### 5.2 Architecture Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Agent Framework** | Strands Agents | AWS-native, best AgentCore integration |
| **Memory Strategy** | Short-term + Long-term | Full conversation context |
| **Frontend Hosting** | S3 + CloudFront | Cost-effective, no compute needed |
| **Tool Protocol** | MCP exclusively | Future-proof, semantic discovery |
| **Identity Provider** | Keep existing (Okta/Cognito) | Minimize OAuth disruption |

### 5.3 CDK Refactoring

```typescript
// Proposed new config structure
interface AgentCoreConfig {
  env: { account: string; region: string };

  // Retained
  ecr: { repositoryName: string };

  // New AgentCore-specific
  agentcore: {
    runtime: {
      agentName: string;
      framework: 'strands';
      sessionMaxHours: 8;
    };
    memory: {
      shortTerm: true;
      longTerm: true;
    };
    gateway: {
      tools: ToolDefinition[];
    };
    identity: {
      provider: 'okta' | 'cognito';
      discoveryUrl: string;
    };
  };

  // New frontend
  frontend: {
    bucketName: string;
    domainName: string;
    certificateArn: string;
  };

  tags: Record<string, string>;
}
```

---

## Appendix A: Current Stack Definitions

### ECR Repository Stack
```typescript
// Current: lib/stacks/ecr-repository-stack.ts
new ecr.Repository(this, 'repository', {
  repositoryName: props.repositoryName,
  imageScanOnPush: true,
  lifecycleRules: [{
    maxImageAge: Duration.days(10),
    tagStatus: ecr.TagStatus.UNTAGGED,
  }],
});
```

### ECS Service Stack (Key Sections)
```typescript
// Current: lib/stacks/ecs-service-stack.ts
const cluster = new ecs.Cluster(this, 'ecs-cluster', {
  vpc,
  clusterName: prefix,
  enableFargateCapacityProviders: true,
  executeCommandConfiguration: { logging: ecs.ExecuteCommandLogging.NONE },
});

const taskDefinition = new ecs.FargateTaskDefinition(this, 'ecs-task-definition', {
  executionRole,
  taskRole,
  memoryLimitMiB: 2048,
  cpu: 1024,
});

// 7 managed policies attached to task role
taskRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonBedrockFullAccess'));
// ... 6 more
```

### RDS Cluster Stack
```typescript
// Current: lib/stacks/rds-cluster-stack.ts
new rds.DatabaseCluster(this, 'rds-cluster', {
  vpc,
  engine: rds.DatabaseClusterEngine.auroraPostgres({ version: rds.AuroraPostgresEngineVersion.VER_16_6 }),
  credentials: rds.Credentials.fromGeneratedSecret('admin'),
  writer: rds.ClusterInstance.serverlessV2('writer'),
  enableDataApi: true,
  serverlessV2MinCapacity: 0,
  serverlessV2MaxCapacity: 1,
});
```

---

## Appendix B: AgentCore API Examples

### Runtime Deployment
```python
# Python SDK example
from bedrock_agentcore import AgentCoreClient

client = AgentCoreClient()

agent = client.create_agent(
    name="nci-oa-agent",
    framework="strands",
    memory_config={
        "short_term": True,
        "long_term": True,
    },
    tools=["brave-search", "gov-info", "translate"],
)
```

### Gateway Tool Registration
```python
# Register Lambda as MCP tool
client.gateway.register_tool(
    name="brave-search",
    type="lambda",
    function_arn="arn:aws:lambda:us-east-1:123456789:function:brave-search",
    description="Search the web using Brave Search API",
    input_schema={
        "query": {"type": "string", "required": True},
        "count": {"type": "integer", "default": 10},
    },
)
```

---

*Report generated: 2026-01-22*
*Author: Claude Code*
*Project: NCI OA Agent - AgentCore Migration*

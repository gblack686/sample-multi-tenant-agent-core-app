#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { EagleCoreStack } from '../lib/core-stack';
import { EagleComputeStack } from '../lib/compute-stack';
import { EagleStorageStack } from '../lib/storage-stack';
import { EagleCiCdStack } from '../lib/cicd-stack';
import { EagleEvalStack } from '../lib/eval-stack';
import { DEV_CONFIG } from '../config/environments';

const app = new cdk.App();
const env = { account: DEV_CONFIG.account, region: DEV_CONFIG.region };

// CI/CD stack is independent — deploy first
const cicd = new EagleCiCdStack(app, 'EagleCiCdStack', {
  env,
  config: DEV_CONFIG,
  description: 'EAGLE CI/CD — GitHub Actions OIDC federation and deploy role',
});

// Core stack: VPC, Cognito, IAM, imports existing S3/DDB
const core = new EagleCoreStack(app, 'EagleCoreStack', {
  env,
  config: DEV_CONFIG,
  description: 'EAGLE Core — VPC, Cognito, IAM, storage imports',
});

// Storage stack is independent of Core (appRole access granted via static ARNs in CoreStack)
const storage = new EagleStorageStack(app, 'EagleStorageStack', {
  env,
  config: DEV_CONFIG,
  description: 'EAGLE Storage — Document bucket, metadata DynamoDB, extraction Lambda',
});

// Compute stack depends on Core for VPC, IAM role, Cognito IDs + Storage for bucket/table names
const compute = new EagleComputeStack(app, 'EagleComputeStack', {
  env,
  config: DEV_CONFIG,
  vpc: core.vpc,
  appRole: core.appRole,
  userPoolId: core.userPool.userPoolId,
  userPoolClientId: core.userPoolClient.userPoolClientId,
  documentBucketName: storage.documentBucket.bucketName,
  metadataTableName: storage.metadataTable.tableName,
  description: 'EAGLE Compute — ECS Fargate, ECR, ALB',
});
compute.addDependency(core);
compute.addDependency(storage);

// Eval stack is independent — no cross-stack dependencies
const evalStack = new EagleEvalStack(app, 'EagleEvalStack', {
  env,
  config: DEV_CONFIG,
  description: 'EAGLE Eval — S3 artifacts, CloudWatch dashboard, SNS alerts',
});

// Tag all stacks
for (const stack of [cicd, core, storage, compute, evalStack]) {
  cdk.Tags.of(stack).add('Project', 'eagle');
  cdk.Tags.of(stack).add('ManagedBy', 'cdk');
  cdk.Tags.of(stack).add('Environment', DEV_CONFIG.env);
}

app.synth();

import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import { EagleConfig } from '../config/environments';

export interface EagleDevboxStackProps extends cdk.StackProps {
  config: EagleConfig;
  vpc: ec2.Vpc;
}

/**
 * EagleDevboxStack — Linux EC2 dev environment for Docker-compliant development.
 *
 * Windows org policy blocks WSL/Docker. This stack provisions a t3.medium Amazon Linux 2023
 * instance in the EAGLE VPC public subnet so developers can SSH in, run Docker natively,
 * build containers, push to ECR, and deploy to Fargate — without touching Docker on Windows.
 *
 * Only deployed when config.enableDevBox === true (DEV only).
 */
export class EagleDevboxStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: EagleDevboxStackProps) {
    super(scope, id, props);
    const { config, vpc } = props;

    // ── IAM Role ──────────────────────────────────────────────────────────────
    const devboxRole = new iam.Role(this, 'DevboxRole', {
      roleName: `eagle-devbox-role-${config.env}`,
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      description: 'IAM role for EAGLE dev box — ECR push, ECS update, Bedrock, DDB, S3',
    });

    // ECR: get login token (account-wide) + push cycle (eagle-* repos only)
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'EcrAuth',
      actions: ['ecr:GetAuthorizationToken'],
      resources: ['*'],
    }));
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'EcrPush',
      actions: [
        'ecr:BatchCheckLayerAvailability',
        'ecr:GetDownloadUrlForLayer',
        'ecr:BatchGetImage',
        'ecr:PutImage',
        'ecr:InitiateLayerUpload',
        'ecr:UploadLayerPart',
        'ecr:CompleteLayerUpload',
        'ecr:DescribeRepositories',
        'ecr:ListImages',
      ],
      resources: [`arn:aws:ecr:${config.region}:${this.account}:repository/eagle-*`],
    }));

    // ECS: update services and describe cluster/services (needed by `just deploy`)
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'EcsUpdate',
      actions: [
        'ecs:UpdateService',
        'ecs:DescribeServices',
        'ecs:DescribeTasks',
        'ecs:ListTasks',
        'ecs:DescribeClusters',
        'ecs:RegisterTaskDefinition',
        'ecs:DeregisterTaskDefinition',
        'ecs:ListTaskDefinitions',
        'ecs:DescribeTaskDefinition',
      ],
      resources: ['*'],
    }));

    // Bedrock: invoke models and cross-region inference profiles
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'BedrockInvoke',
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
      ],
      resources: [
        'arn:aws:bedrock:*::foundation-model/anthropic.*',
        `arn:aws:bedrock:${config.region}:${this.account}:inference-profile/us.anthropic.*`,
      ],
    }));

    // DynamoDB: CRUD on eagle tables (using ARN strings to avoid cross-stack cycles)
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'DynamoDBAccess',
      actions: [
        'dynamodb:GetItem',
        'dynamodb:PutItem',
        'dynamodb:UpdateItem',
        'dynamodb:DeleteItem',
        'dynamodb:Query',
        'dynamodb:Scan',
        'dynamodb:BatchWriteItem',
      ],
      resources: [
        `arn:aws:dynamodb:${config.region}:${this.account}:table/${config.eagleTableName}`,
        `arn:aws:dynamodb:${config.region}:${this.account}:table/${config.eagleTableName}/index/*`,
        `arn:aws:dynamodb:${config.region}:${this.account}:table/${config.documentMetadataTableName}`,
        `arn:aws:dynamodb:${config.region}:${this.account}:table/${config.documentMetadataTableName}/index/*`,
      ],
    }));

    // S3: document buckets + CDK asset buckets (for cdk deploy from devbox)
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'S3Access',
      actions: [
        's3:GetObject',
        's3:PutObject',
        's3:DeleteObject',
        's3:ListBucket',
      ],
      resources: [
        `arn:aws:s3:::${config.docsBucketName}`,
        `arn:aws:s3:::${config.docsBucketName}/*`,
        `arn:aws:s3:::${config.documentBucketName}`,
        `arn:aws:s3:::${config.documentBucketName}/*`,
        `arn:aws:s3:::cdk-*`,
        `arn:aws:s3:::cdk-*/*`,
      ],
    }));

    // CloudWatch Logs: tail ECS logs via `just logs`
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'CloudWatchLogs',
      actions: [
        'logs:GetLogEvents',
        'logs:FilterLogEvents',
        'logs:DescribeLogGroups',
        'logs:DescribeLogStreams',
        'logs:CreateLogStream',
        'logs:PutLogEvents',
      ],
      resources: [
        `arn:aws:logs:${config.region}:${this.account}:log-group:/eagle/*`,
        `arn:aws:logs:${config.region}:${this.account}:log-group:/eagle/*:*`,
      ],
    }));

    // CloudFormation: CDK synth/diff/deploy from devbox
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'CloudFormation',
      actions: [
        'cloudformation:DescribeStacks',
        'cloudformation:ListStacks',
        'cloudformation:GetTemplate',
        'cloudformation:DescribeStackEvents',
      ],
      resources: ['*'],
    }));

    // SSM: read CDK bootstrap parameter
    devboxRole.addToPolicy(new iam.PolicyStatement({
      sid: 'SsmRead',
      actions: ['ssm:GetParameter'],
      resources: [`arn:aws:ssm:${config.region}:${this.account}:parameter/cdk-bootstrap/*`],
    }));

    // ── Security Group ────────────────────────────────────────────────────────
    const sg = new ec2.SecurityGroup(this, 'DevboxSg', {
      securityGroupName: `eagle-devbox-sg-${config.env}`,
      vpc,
      description: 'EAGLE dev box — SSH ingress',
      allowAllOutbound: true,
    });

    // IMPORTANT: Restrict devboxSshCidr in environments.ts to your VPN/IP range.
    // Default 0.0.0.0/0 is intentionally permissive for initial setup — tighten before prod.
    sg.addIngressRule(
      ec2.Peer.ipv4(config.devboxSshCidr ?? '0.0.0.0/0'),
      ec2.Port.tcp(22),
      'SSH — set config.devboxSshCidr to restrict access',
    );

    // ── User Data (bootstrap script) ──────────────────────────────────────────
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      'set -e',
      'exec > >(tee /var/log/user-data.log) 2>&1',
      '',
      '# System updates',
      'dnf update -y',
      '',
      '# Docker (native on Amazon Linux 2023)',
      'dnf install -y docker git',
      'systemctl enable docker',
      'systemctl start docker',
      'usermod -aG docker ec2-user',
      '',
      '# Docker Compose v2 plugin',
      'mkdir -p /usr/local/lib/docker/cli-plugins',
      'curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \\',
      '  -o /usr/local/lib/docker/cli-plugins/docker-compose',
      'chmod +x /usr/local/lib/docker/cli-plugins/docker-compose',
      '',
      '# Node 20 (for CDK)',
      'dnf install -y nodejs npm',
      '',
      '# Python pip (Python 3.11 pre-installed on AL2023)',
      'python3 -m ensurepip --upgrade',
      '',
      '# just task runner',
      'curl -fsSL https://just.systems/install.sh | bash -s -- --to /usr/local/bin',
      '',
      '# Helpful aliases for ec2-user',
      'echo "alias dc=\'docker compose\'" >> /home/ec2-user/.bashrc',
      'echo "export AWS_REGION=us-east-1" >> /home/ec2-user/.bashrc',
      '',
      'echo "Bootstrap complete — reboot or re-login for docker group to take effect"',
    );

    // ── EC2 Instance ──────────────────────────────────────────────────────────
    const instance = new ec2.Instance(this, 'DevboxInstance', {
      instanceName: `eagle-devbox-${config.env}`,
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
      machineImage: ec2.MachineImage.latestAmazonLinux2023(),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroup: sg,
      role: devboxRole,
      userData,
      blockDevices: [{
        deviceName: '/dev/xvda',
        volume: ec2.BlockDeviceVolume.ebs(50, {
          volumeType: ec2.EbsDeviceVolumeType.GP3,
          encrypted: true,
          deleteOnTermination: true,
        }),
      }],
      requireImdsv2: true,  // IMDSv2 enforced — more secure against SSRF
    });

    // ── Elastic IP (stable public IP across stop/start) ───────────────────────
    const eip = new ec2.CfnEIP(this, 'DevboxEip', {
      domain: 'vpc',
      tags: [{ key: 'Name', value: `eagle-devbox-eip-${config.env}` }],
    });

    new ec2.CfnEIPAssociation(this, 'DevboxEipAssoc', {
      instanceId: instance.instanceId,
      allocationId: eip.attrAllocationId,
    });

    // ── Outputs ───────────────────────────────────────────────────────────────
    new cdk.CfnOutput(this, 'DevboxPublicIp', {
      value: eip.ref,
      description: 'Elastic IP — SSH target for the EAGLE dev box',
      exportName: `eagle-devbox-ip-${config.env}`,
    });

    new cdk.CfnOutput(this, 'SshCommand', {
      value: `ssh -i ~/.ssh/eagle-dev-box.pem ec2-user@${eip.ref}`,
      description: 'SSH command to connect to the EAGLE dev box',
    });

    new cdk.CfnOutput(this, 'DevboxInstanceId', {
      value: instance.instanceId,
      description: 'EC2 instance ID — use to stop/start via AWS CLI',
      exportName: `eagle-devbox-instance-id-${config.env}`,
    });

    new cdk.CfnOutput(this, 'StopCommand', {
      value: `aws ec2 stop-instances --instance-ids ${instance.instanceId}`,
      description: 'Stop the dev box when not in use (~$0.04/hr saved)',
    });
  }
}

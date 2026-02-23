# Plan: EC2 Linux Dev Environment (Docker-Compliant)

## Task Description
Set up a Linux EC2 instance as the primary development environment for EAGLE. The Windows
development machine cannot run Docker due to org policy (WSL/Docker blocked). The EC2 instance
acts as a compliant, always-on Linux dev box — SSH'd into from Windows — where Docker runs
natively. Code is built, tested, and pushed to ECR from there, then deployed to ECS Fargate.

## Objective
Developer SSHs into a Linux EC2 instance from Windows, runs `just dev` / `just deploy` exactly
as documented, and the experience is identical to a native Linux dev machine. Zero Docker on
Windows. Zero compliance concerns.

## Problem Statement
- Windows org policy blocks WSL and Docker
- EAGLE's CI/CD pipeline (`just dev`, `just deploy`) starts with `docker build`
- Running Docker in the cloud on a Windows host (nested VM) violates org guidance
- Need a Linux environment that is close to the Fargate runtime for consistent dev/prod parity

## Solution Approach
Launch a **t3.medium EC2 instance** (Amazon Linux 2023) in the existing EAGLE VPC. Attach an
IAM instance profile with ECR push + ECS update permissions. SSH in from Windows PowerShell
using a key pair. The existing `Justfile` commands (`just dev`, `just deploy`, `just eval`)
work unmodified because Docker runs natively on Linux.

---

## Relevant Files

- `infrastructure/cdk-eagle/lib/core-stack.ts` — VPC and IAM role to reference
- `infrastructure/cdk-eagle/config/environments.ts` — Account ID and region (`us-east-1`)
- `deployment/docker-compose.dev.yml` — Local dev stack; runs on EC2 as-is
- `deployment/docker/Dockerfile.backend` — Backend container build context
- `deployment/docker/Dockerfile.frontend` — Frontend container build context
- `Justfile` — All dev/deploy commands (`just dev`, `just deploy`, `just eval`)
- `.github/workflows/deploy.yml` — Reference for ECR repo names and ECS service names

### New Files
- `infrastructure/cdk-eagle/lib/devbox-stack.ts` — Optional: CDK stack to codify the EC2 dev box
- `deployment/scripts/bootstrap-ec2.sh` — User data script to install Docker, Git, Just, Node, Python

---

## Implementation Phases

### Phase 1: Foundation — Launch EC2 + Configure Access
Spin up the instance, configure SSH, attach IAM role, verify connectivity from Windows.

### Phase 2: Dev Environment Setup — Install Toolchain
Install Docker, Git, Node 20, Python 3.11, AWS CLI v2, `just`, clone the repo.

### Phase 3: Integration — Wire to ECR/ECS and Validate
`docker login` to ECR via instance profile, run `just dev`, run `just deploy`, verify Fargate
picks up the new image.

---

## Step by Step Tasks

### 1. Create EC2 Key Pair (Windows)
- Open PowerShell on Windows
- Run: `aws ec2 create-key-pair --key-name eagle-dev-box --query 'KeyMaterial' --output text > %USERPROFILE%\.ssh\eagle-dev-box.pem`
- Set permissions: `icacls %USERPROFILE%\.ssh\eagle-dev-box.pem /inheritance:r /grant:r "%USERNAME%:R"`
- Store the `.pem` file safely — you cannot re-download it

### 2. Create Security Group
- Allow SSH (port 22) from **your IP only**: `aws ec2 create-security-group --group-name eagle-devbox-sg --description "EAGLE dev box SSH access"`
- Add inbound SSH rule: `aws ec2 authorize-security-group-ingress --group-name eagle-devbox-sg --protocol tcp --port 22 --cidr $(curl -s https://checkip.amazonaws.com)/32`
- For `just dev` local access, also allow port 8000 and 3000 from your IP (optional)

### 3. Create IAM Instance Profile
Create a policy and attach to a new instance profile role:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["ecr:GetAuthorizationToken"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["ecr:BatchCheckLayerAvailability","ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage","ecr:PutImage","ecr:InitiateLayerUpload","ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"],
      "Resource": "arn:aws:ecr:us-east-1:*:repository/eagle-*" },
    { "Effect": "Allow", "Action": ["ecs:UpdateService","ecs:DescribeServices","ecs:DescribeTasks",
        "ecs:ListTasks"],
      "Resource": "*" },
    { "Effect": "Allow", "Action": ["logs:GetLogEvents","logs:FilterLogEvents"],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/ecs/eagle-*:*" },
    { "Effect": "Allow", "Action": ["s3:GetObject","s3:PutObject","s3:ListBucket"],
      "Resource": ["arn:aws:s3:::cdk-*","arn:aws:s3:::cdk-*/*","arn:aws:s3:::nci-documents*",
        "arn:aws:s3:::nci-documents*/*"] },
    { "Effect": "Allow", "Action": ["cloudformation:DescribeStacks","cloudformation:ListStacks"],
      "Resource": "*" },
    { "Effect": "Allow", "Action": ["dynamodb:GetItem","dynamodb:PutItem","dynamodb:Query",
        "dynamodb:Scan","dynamodb:UpdateItem","dynamodb:DeleteItem"],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/eagle*" },
    { "Effect": "Allow", "Action": ["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],
      "Resource": "*" }
  ]
}
```
- `aws iam create-role --role-name eagle-devbox-role --assume-role-policy-document file://trust-ec2.json`
- `aws iam put-role-policy --role-name eagle-devbox-role --policy-name eagle-devbox-policy --policy-document file://devbox-policy.json`
- `aws iam create-instance-profile --instance-profile-name eagle-devbox-profile`
- `aws iam add-role-to-instance-profile --instance-profile-name eagle-devbox-profile --role-name eagle-devbox-role`

### 4. Launch EC2 Instance
```bash
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \   # Amazon Linux 2023 us-east-1
  --instance-type t3.medium \
  --key-name eagle-dev-box \
  --security-groups eagle-devbox-sg \
  --iam-instance-profile Name=eagle-devbox-profile \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=eagle-devbox-dev}]' \
  --user-data file://deployment/scripts/bootstrap-ec2.sh
```
- 50 GB gp3 root volume (Docker images are large)
- `t3.medium` = 2 vCPU / 4 GB RAM (sufficient for `docker compose up` with backend + frontend)

### 5. Create Bootstrap Script (`deployment/scripts/bootstrap-ec2.sh`)
```bash
#!/bin/bash
set -e

# System updates
dnf update -y

# Docker (native on Amazon Linux 2023)
dnf install -y docker git
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# Docker Compose v2 plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Node 20 (for CDK)
dnf install -y nodejs npm

# Python 3.11 (pre-installed on AL2023, ensure pip)
python3 -m ensurepip --upgrade

# AWS CLI v2 (pre-installed on AL2023)
aws --version

# just (task runner)
curl -fsSL https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Playwright dependencies (for smoke tests)
dnf install -y chromium

echo "Bootstrap complete"
```

### 6. SSH into the Instance from Windows
- Get public IP: `aws ec2 describe-instances --filters "Name=tag:Name,Values=eagle-devbox-dev" --query 'Reservations[].Instances[].PublicIpAddress' --output text`
- Connect: `ssh -i %USERPROFILE%\.ssh\eagle-dev-box.pem ec2-user@<PUBLIC_IP>`
- **VS Code Remote SSH** (recommended): Install `Remote - SSH` extension, add host to `~/.ssh/config`:
  ```
  Host eagle-devbox
      HostName <PUBLIC_IP>
      User ec2-user
      IdentityFile ~/.ssh/eagle-dev-box.pem
  ```

### 7. Clone the Repository on EC2
```bash
# Configure git (first time)
git config --global user.name "Your Name"
git config --global user.email "your@nih.gov"

# Clone sm_eagle (CBIIT repo)
git clone https://github.com/CBIIT/sm_eagle.git ~/eagle
cd ~/eagle
git checkout dev/greg
```
- Use a GitHub Personal Access Token (PAT) for HTTPS auth, or set up SSH keys for GitHub

### 8. Configure Environment Variables
```bash
cd ~/eagle
cp server/.env.example server/.env  # if exists, or create manually
```
Create `server/.env`:
```
AWS_REGION=us-east-1
DYNAMODB_TABLE=eagle
COGNITO_USER_POOL_ID=<from CDK output>
COGNITO_CLIENT_ID=<from CDK output>
S3_BUCKET=<nci-documents bucket name>
```
Frontend env:
```bash
cat > client/.env.local <<EOF
NEXT_PUBLIC_COGNITO_USER_POOL_ID=<from CDK output>
NEXT_PUBLIC_COGNITO_CLIENT_ID=<from CDK output>
NEXT_PUBLIC_COGNITO_REGION=us-east-1
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

### 9. Verify Docker + ECR Login
```bash
# Confirm Docker works
docker run --rm hello-world

# Login to ECR using instance profile (no credentials needed)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Verify ECR repos are accessible
aws ecr describe-repositories --region us-east-1
```

### 10. Run Local Dev Stack
```bash
cd ~/eagle

# Start full stack (hot reload)
just dev

# Or detached
just dev-up

# Verify backend health
curl http://localhost:8000/api/health

# Tail logs
just logs backend
```

### 11. Build and Deploy to Fargate
```bash
cd ~/eagle

# Build containers locally on EC2
just build-backend
just build-frontend

# Full deploy: build → ECR push → ECS force-new-deployment → wait
just deploy

# Check Fargate service status
just status
```

### 12. (Optional) Add to CDK as DevboxStack
Create `infrastructure/cdk-eagle/lib/devbox-stack.ts`:
- EC2 instance resource (only provisioned in dev env)
- Security group (SSH from VPN CIDR)
- IAM instance profile
- Outputs: public IP, SSH command
- Gate with `config.enableDevBox?: boolean` in `environments.ts`

---

## Testing Strategy

- SSH connectivity from Windows PowerShell
- `docker run hello-world` on EC2
- `just dev` — both containers start, `/api/health` returns 200
- `just deploy` — ECR push succeeds, ECS service reaches steady state
- `just eval` — all 28 tests pass (or match baseline)

---

## Acceptance Criteria

- [ ] Can SSH into EC2 from Windows PowerShell with key pair
- [ ] `docker ps` works without `sudo` (ec2-user in docker group)
- [ ] `aws ecr get-login-password` succeeds using instance profile (no `aws configure` needed)
- [ ] `just dev-up` starts backend and frontend containers successfully
- [ ] `curl http://localhost:8000/api/health` returns `{"status": "ok"}`
- [ ] `just deploy` pushes images to ECR and ECS service reaches steady state
- [ ] No Docker installed on Windows development machine

---

## Validation Commands

```bash
# 1. Verify instance profile credentials (no secrets needed)
aws sts get-caller-identity

# 2. Verify Docker
docker run --rm hello-world

# 3. Verify ECR access
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 4. Verify dev stack
just dev-up && sleep 10 && curl -f http://localhost:8000/api/health

# 5. Verify deploy pipeline
just deploy && just status
```

---

## Notes

- **Cost**: t3.medium = ~$0.0416/hr (~$30/mo). Stop the instance when not in use (`aws ec2 stop-instances`).
  Add to Justfile: `just devbox-stop` / `just devbox-start` for convenience.
- **Elastic IP**: Assign an Elastic IP so the public IP doesn't change on restart ($0 when associated).
- **Placement**: Launch in the same VPC/region as Fargate to minimize latency to DynamoDB/S3.
  Use a public subnet (needs internet access for `docker pull`, GitHub).
- **Security Group hygiene**: Restrict SSH to VPN CIDR or your static IP only. Audit monthly.
- **VS Code Remote SSH** gives full IDE experience on the EC2 — strongly recommended over terminal-only.
- **GitHub auth on EC2**: Use a fine-grained PAT scoped to `CBIIT/sm_eagle` (read+write), or
  add EC2's SSH public key to your GitHub account.
- **Instance profile > SSO**: The instance profile handles all AWS API calls automatically.
  No `aws configure`, no token refresh, no credential files needed.
- **Justfile hot reload**: `docker-compose.dev.yml` mounts source dirs as volumes, so edits on
  the EC2 (or via VS Code Remote SSH) are reflected immediately without rebuilding.
```

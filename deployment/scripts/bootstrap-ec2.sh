#!/bin/bash
# EAGLE Dev Box Bootstrap Script
# Runs as EC2 user data on first boot (Amazon Linux 2023)
# Installs: Docker, Docker Compose v2, Node 20, Python pip, just task runner
# Log: /var/log/user-data.log

set -e
exec > >(tee /var/log/user-data.log) 2>&1

echo "=== EAGLE Dev Box Bootstrap ==="
echo "Started: $(date)"

# ── System updates ─────────────────────────────────────────────────────────────
dnf update -y

# ── Docker (native on Amazon Linux 2023) ──────────────────────────────────────
dnf install -y docker git curl
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user
echo "Docker: $(docker --version)"

# ── Docker Compose v2 plugin ───────────────────────────────────────────────────
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
echo "Docker Compose: $(docker compose version)"

# ── Node 20 (for CDK and frontend builds) ─────────────────────────────────────
dnf install -y nodejs npm
echo "Node: $(node --version)"
echo "npm: $(npm --version)"

# Install AWS CDK globally
npm install -g aws-cdk typescript ts-node
echo "CDK: $(cdk --version)"

# ── Python pip (Python 3.11 pre-installed on AL2023) ──────────────────────────
python3 -m ensurepip --upgrade
pip3 install --upgrade pip
echo "Python: $(python3 --version)"

# ── just task runner ───────────────────────────────────────────────────────────
curl -fsSL https://just.systems/install.sh | bash -s -- --to /usr/local/bin
echo "just: $(just --version)"

# ── Helpful shell config for ec2-user ─────────────────────────────────────────
cat >> /home/ec2-user/.bashrc << 'BASHRC'

# EAGLE dev box
export AWS_REGION=us-east-1
alias dc='docker compose'
alias ll='ls -la'

# ECR login helper
ecr-login() {
  ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    "${ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com"
  echo "Logged in to ECR: ${ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com"
}
BASHRC

chown ec2-user:ec2-user /home/ec2-user/.bashrc

echo ""
echo "=== Bootstrap complete: $(date) ==="
echo "NOTE: Log out and back in (or run 'newgrp docker') for docker group to take effect"
echo ""
echo "Quick start:"
echo "  git clone https://github.com/CBIIT/sm_eagle.git ~/eagle"
echo "  cd ~/eagle && git checkout dev/greg"
echo "  ecr-login"
echo "  just dev-up"

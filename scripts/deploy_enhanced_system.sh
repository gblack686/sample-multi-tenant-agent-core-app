#!/bin/bash
set -e

echo "🚀 Deploying Enhanced MCP-Agent Core Multi-Tenant System"
echo "========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}📋 Checking Prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI${NC}"
    exit 1
fi

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo -e "${YELLOW}⚠️  CDK not found. Installing...${NC}"
    npm install -g aws-cdk
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3${NC}"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure'${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo -e "${BLUE}📍 Deploying to Account: ${AWS_ACCOUNT}, Region: ${AWS_REGION}${NC}"

# Step 1: Deploy Infrastructure
echo -e "${BLUE}🏗️  Step 1: Deploying Infrastructure...${NC}"
cd infra/cdk

# Install Python dependencies
echo "Installing CDK dependencies..."
pip install -r requirements.txt

# Bootstrap CDK (idempotent)
echo "Bootstrapping CDK..."
cdk bootstrap aws://${AWS_ACCOUNT}/${AWS_REGION}

# Deploy stack
echo "Deploying CDK stack..."
cdk deploy --require-approval never --outputs-file outputs.json

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
else
    echo -e "${RED}❌ Infrastructure deployment failed${NC}"
    exit 1
fi

# Extract outputs
USER_POOL_ID=$(jq -r '.MultiTenantBedrockStack.UserPoolId' outputs.json)
CLIENT_ID=$(jq -r '.MultiTenantBedrockStack.UserPoolClientId' outputs.json)

echo -e "${GREEN}📋 CDK Outputs:${NC}"
echo "   User Pool ID: ${USER_POOL_ID}"
echo "   Client ID: ${CLIENT_ID}"

# Go back to root
cd ../..

# Step 2: Create Bedrock Agent (Optional)
echo -e "${BLUE}🤖 Step 2: Creating Bedrock Agent...${NC}"
python scripts/create_bedrock_agent.py > bedrock_agent_output.txt 2>&1 || echo "Bedrock Agent creation failed, using fallback"

# Extract Agent ID
if [ -f "bedrock_agent_output.txt" ]; then
    AGENT_ID=$(grep "Agent ID:" bedrock_agent_output.txt | cut -d':' -f2 | xargs || echo "fallback-direct-model")
else
    AGENT_ID="fallback-direct-model"
fi

echo "   Agent ID: ${AGENT_ID}"

# Step 3: Set Environment Variables
echo -e "${BLUE}🔧 Step 3: Setting Environment Variables...${NC}"

# Create .env file
cat > .env << EOF
# Cognito Configuration
COGNITO_USER_POOL_ID=${USER_POOL_ID}
COGNITO_CLIENT_ID=${CLIENT_ID}

# DynamoDB Tables
SESSIONS_TABLE=tenant-sessions
USAGE_TABLE=tenant-usage

# Bedrock Agent
BEDROCK_AGENT_ID=${AGENT_ID}
BEDROCK_AGENT_ALIAS_ID=TSTALIASID

# AWS Configuration
AWS_REGION=${AWS_REGION}

# Application Configuration
ENVIRONMENT=development
JWT_SECRET=dev-secret-key
EOF

echo -e "${GREEN}✅ Environment variables saved to .env${NC}"

# Step 4: Install Application Dependencies
echo -e "${BLUE}📦 Step 4: Installing Application Dependencies...${NC}"
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Step 5: Create Test Users with Subscription Tiers
echo -e "${BLUE}👥 Step 5: Creating Multi-Tier Test Users...${NC}"

export COGNITO_USER_POOL_ID=${USER_POOL_ID}
export COGNITO_CLIENT_ID=${CLIENT_ID}

python scripts/create_test_users_with_tiers.py > test_users_output.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test users created successfully${NC}"
    echo -e "${YELLOW}📝 JWT tokens saved to test_users_output.txt${NC}"
else
    echo -e "${RED}❌ Failed to create test users${NC}"
    echo "Check test_users_output.txt for details"
fi

# Step 6: Test MCP-Agent Integration
echo -e "${BLUE}🧪 Step 6: Testing MCP-Agent Integration...${NC}"
python examples/mcp_agent_demo.py > integration_test_output.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ MCP-Agent integration test passed${NC}"
else
    echo -e "${YELLOW}⚠️  Integration test had issues (check integration_test_output.txt)${NC}"
fi

# Step 7: Start Application
echo -e "${BLUE}🚀 Step 7: Starting Application...${NC}"

# Create startup script
cat > start_app.sh << 'EOF'
#!/bin/bash
source .env 2>/dev/null || true
export $(grep -v '^#' .env | xargs) 2>/dev/null || true
echo "🚀 Starting Enhanced MCP-Agent Core Multi-Tenant System..."
echo "📍 Visit: http://localhost:8000"
echo "🔑 Use JWT tokens from test_users_output.txt"
python run.py
EOF

chmod +x start_app.sh

# Final Summary
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "   ✅ Infrastructure: MultiTenantBedrockStack"
echo "   ✅ User Pool ID: ${USER_POOL_ID}"
echo "   ✅ Client ID: ${CLIENT_ID}"
echo "   ✅ Agent ID: ${AGENT_ID}"
echo "   ✅ Test Users: Created with all tiers"
echo "   ✅ MCP Integration: Ready"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "   1. Start the application:"
echo "      ./start_app.sh"
echo ""
echo "   2. Visit the application:"
echo "      http://localhost:8000"
echo ""
echo "   3. Use test JWT tokens from:"
echo "      cat test_users_output.txt"
echo ""
echo -e "${BLUE}🧪 Testing Commands:${NC}"
echo "   # Test MCP integration"
echo "   python examples/mcp_agent_demo.py"
echo ""
echo "   # Test API endpoints"
echo "   curl http://localhost:8000/api/mcp/tools \\"
echo "     -H \"Authorization: Bearer <jwt-token>\""
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "   - README_SUBSCRIPTION_TIERS.md"
echo "   - README_MCP_AGENT_INTEGRATION.md"
echo "   - DEPLOYMENT_GUIDE.md"
echo ""
echo -e "${GREEN}🎯 The enhanced MCP-Agent Core system is ready!${NC}"
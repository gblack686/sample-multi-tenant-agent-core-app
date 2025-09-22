# Multi-Tenant Frontend Application

## 🖥️ **Real User Authentication & Multi-Tenant Testing**

### **Features:**
- ✅ **Cognito Authentication** - Real user login/registration
- ✅ **Multi-Tenant Support** - Users belong to different organizations
- ✅ **Session Management** - Persistent chat sessions per tenant
- ✅ **Usage Analytics** - View tenant-specific usage data
- ✅ **Agentic Capabilities** - Full Bedrock Agent Core integration

## 🚀 **How to Use:**

### **1. After Deployment:**
The GitHub Actions workflow automatically configures the frontend with your deployed Cognito User Pool.

### **2. Open Frontend:**
```bash
# Serve the frontend (simple HTTP server)
cd frontend
python -m http.server 8080

# Or use any web server
# Open: http://localhost:8080
```

### **3. Register Users:**
Create real users for different organizations:

**Acme Corporation Users:**
- Email: `john@acme.com`, Organization: `acme-corp`
- Email: `jane@acme.com`, Organization: `acme-corp`

**Beta Industries Users:**
- Email: `bob@beta.com`, Organization: `beta-inc`
- Email: `alice@beta.com`, Organization: `beta-inc`

**Gamma LLC Users:**
- Email: `charlie@gamma.com`, Organization: `gamma-llc`

### **4. Test Multi-Tenancy:**

#### **Login as Different Users:**
1. **Register/Login** as `john@acme.com` (Acme Corp)
2. **Chat** with the AI assistant
3. **View Usage** - See Acme Corp metrics
4. **Logout** and **Login** as `bob@beta.com` (Beta Inc)
5. **Chat** and **View Usage** - See Beta Inc metrics (isolated)

#### **Verify Tenant Isolation:**
- Each organization sees only their own:
  - Chat sessions
  - Usage metrics
  - User data
- Complete data isolation between tenants

## 🔧 **Configuration:**

The frontend automatically gets configured with:
```javascript
const CONFIG = {
    userPoolId: 'us-east-1_ABC123DEF',  // From deployment
    clientId: 'abc123def456ghi789',     // From deployment
    region: 'us-east-1',
    apiUrl: 'http://localhost:8000'     // Backend API
};
```

## 🧪 **Multi-Tenant Testing Scenarios:**

### **Scenario 1: Different Organizations**
1. Register users from different companies
2. Login and chat from each organization
3. Verify complete data isolation

### **Scenario 2: Same Organization, Multiple Users**
1. Register multiple users for same organization
2. Login as different users from same tenant
3. Verify shared tenant context but separate user sessions

### **Scenario 3: Usage Analytics**
1. Generate different usage patterns per tenant
2. View usage analytics for each organization
3. Verify tenant-specific metrics tracking

## 🎯 **What This Demonstrates:**

- ✅ **Real Authentication** - No dummy data, actual Cognito users
- ✅ **Tenant Isolation** - Complete separation between organizations
- ✅ **Session Management** - Persistent sessions per tenant-user
- ✅ **Usage Tracking** - Real-time analytics per tenant
- ✅ **Agentic Features** - Full Bedrock Agent Core capabilities
- ✅ **Production Ready** - Real-world multi-tenant architecture

**This frontend provides a complete multi-tenant testing environment with real user authentication and tenant isolation!**
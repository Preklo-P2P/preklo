# Preklo Deployment Strategy

**Domain**: preklo.rowellholdings.co.za  
**Created**: October 17, 2025  
**Strategy**: Multi-environment with Git branching

---

## 🌳 Git Branching Strategy

### **Branch Structure**

```
main (production)
  ├── Tagged releases (v1.0.0, v1.1.0, etc.)
  └── Protected branch - requires PR approval
  
development (staging)
  ├── Active development
  ├── Testing ground
  └── Auto-deploys to dev environment
  
feature/* (feature branches)
  └── Individual features, merge to development
```

### **Branch Details**

| Branch | Environment | URL | Purpose | Auto-Deploy |
|--------|-------------|-----|---------|-------------|
| `main` | Production | preklo.rowellholdings.co.za | Stable, public release | Yes |
| `development` | Staging | dev.preklo.rowellholdings.co.za | Testing, QA | Yes |
| `feature/*` | Local | localhost | Development | No |

---

## 🚀 Setting Up Branches

### **Step 1: Create Development Branch**

```bash
cd /home/davey/Documents/rowell/dev/preklo

# Make sure you're on main and it's up to date
git checkout main
git pull origin main

# Create development branch from main
git checkout -b development

# Push development branch to remote
git push -u origin development

# Go back to main
git checkout main
```

### **Step 2: Set Branch Protection Rules (GitHub)**

1. Go to: `https://github.com/yourusername/preklo/settings/branches`

2. **Protect `main` branch**:
   - Add rule for `main`
   - ✅ Require pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass
   - ✅ Do not allow bypassing

3. **Protect `development` branch** (optional but recommended):
   - Add rule for `development`
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass

---

## 🌐 Domain Configuration

### **DNS Setup**

You need to configure DNS records for `rowellholdings.co.za`:

```
# Production
A     preklo.rowellholdings.co.za     →  [Vercel IP or CNAME]
CNAME preklo.rowellholdings.co.za     →  cname.vercel-dns.com

# Development (Staging)
CNAME dev.preklo.rowellholdings.co.za →  cname.vercel-dns.com
```

**Or use subdomains on different platforms:**
```
# Frontend
preklo.rowellholdings.co.za          → Vercel
dev.preklo.rowellholdings.co.za      → Vercel

# Backend
api.preklo.rowellholdings.co.za      → Railway
api-dev.preklo.rowellholdings.co.za  → Railway
```

---

## 🏗️ Deployment Configuration

### **Environment 1: Development (Staging)**

#### **Backend - Railway (Development)**

1. **Create Railway Project**: `preklo-backend-dev`
2. **Connect to Git**: Link to `development` branch
3. **Environment Variables**:
   ```
   DATABASE_URL=${DATABASE_URL}  # Railway auto-provides
   JWT_SECRET_KEY=<dev-secret-different-from-prod>
   APTOS_NODE_URL=https://fullnode.testnet.aptoslabs.com/v1
   APTOS_PRIVATE_KEY=<dev-testnet-private-key>
   APTOS_CONTRACT_ADDRESS=0xa3bbeb9cc35bab4c3c0af22c9b1398e4d849d4b33ed59b59a6dc4b1ca5298a2d
   PROJECT_NAME=Preklo (Development)
   DEBUG=True
   API_V1_STR=/api/v1
   ENVIRONMENT=development
   ```

4. **Custom Domain**: `api-dev.preklo.rowellholdings.co.za`

#### **Frontend - Vercel (Development)**

1. **Create Vercel Project**: `preklo-frontend-dev`
2. **Connect to Git**: Link to `development` branch
3. **Build Settings**:
   ```
   Framework Preset: Vite
   Build Command: npm run build
   Output Directory: dist
   Install Command: npm install
   ```

4. **Environment Variables**:
   ```
   VITE_API_BASE_URL=https://api-dev.preklo.rowellholdings.co.za
   VITE_APP_NAME=Preklo (Dev)
   VITE_APP_VERSION=1.0.0-dev
   VITE_ENVIRONMENT=development
   ```

5. **Custom Domain**: `dev.preklo.rowellholdings.co.za`

---

### **Environment 2: Production**

#### **Backend - Railway (Production)**

1. **Create Railway Project**: `preklo-backend-prod`
2. **Connect to Git**: Link to `main` branch
3. **Environment Variables**:
   ```
   DATABASE_URL=${DATABASE_URL}  # Railway auto-provides
   JWT_SECRET_KEY=<strong-production-secret>
   APTOS_NODE_URL=https://fullnode.testnet.aptoslabs.com/v1
   APTOS_PRIVATE_KEY=<prod-testnet-private-key>
   APTOS_CONTRACT_ADDRESS=0xa3bbeb9cc35bab4c3c0af22c9b1398e4d849d4b33ed59b59a6dc4b1ca5298a2d
   PROJECT_NAME=Preklo
   DEBUG=False
   API_V1_STR=/api/v1
   ENVIRONMENT=production
   ```

4. **Custom Domain**: `api.preklo.rowellholdings.co.za`

#### **Frontend - Vercel (Production)**

1. **Create Vercel Project**: `preklo-frontend-prod`
2. **Connect to Git**: Link to `main` branch
3. **Build Settings**: Same as dev

4. **Environment Variables**:
   ```
   VITE_API_BASE_URL=https://api.preklo.rowellholdings.co.za
   VITE_APP_NAME=Preklo
   VITE_APP_VERSION=1.0.0
   VITE_ENVIRONMENT=production
   ```

5. **Custom Domain**: `preklo.rowellholdings.co.za`

---

## 🔄 Workflow

### **Daily Development Workflow**

```bash
# 1. Start with development branch
git checkout development
git pull origin development

# 2. Create feature branch
git checkout -b feature/add-new-feature

# 3. Make changes, commit
git add .
git commit -m "feat: add new feature"

# 4. Push feature branch
git push origin feature/add-new-feature

# 5. Create PR: feature/add-new-feature → development
# 6. After PR approval, merge to development
# 7. Development branch auto-deploys to dev.preklo.rowellholdings.co.za

# 8. Test on dev environment
# 9. If all good, create PR: development → main

# 10. After PR approval, merge to main
# 11. Main branch auto-deploys to preklo.rowellholdings.co.za
```

### **Release Workflow**

```bash
# When development is stable and tested:

# 1. Create PR from development to main
git checkout development
git pull origin development

# 2. On GitHub, create PR: development → main
# Title: "Release v1.1.0: New Features"
# Description: List changes

# 3. Review and approve PR

# 4. Merge to main (squash or merge commit)

# 5. Tag the release
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 6. Production auto-deploys!
```

### **Hotfix Workflow** (Critical bugs in production)

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# 2. Fix the bug
git add .
git commit -m "fix: critical bug in payment processing"

# 3. Create PR: hotfix/critical-bug-fix → main
git push origin hotfix/critical-bug-fix

# 4. After approval, merge to main
# 5. Production deploys

# 6. Merge hotfix back to development
git checkout development
git merge main
git push origin development
```

---

## 📋 Environment Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| **Purpose** | Testing, QA | Public users |
| **Branch** | `development` | `main` |
| **Domain** | dev.preklo.rowellholdings.co.za | preklo.rowellholdings.co.za |
| **Backend** | api-dev.preklo.rowellholdings.co.za | api.preklo.rowellholdings.co.za |
| **Database** | Separate dev database | Production database |
| **Debug Mode** | True | False |
| **Data** | Test data, can be reset | Real user data |
| **Updates** | Frequent, every merge | Controlled releases |
| **JWT Secret** | Development secret | Strong production secret |
| **Wallet Keys** | Test keys | Secure production keys |

---

## 🛡️ Security Considerations

### **Different Secrets per Environment**

```bash
# Generate different JWT secrets for each environment
# Development:
python3 -c "import secrets; print('DEV:', secrets.token_urlsafe(64))"

# Production:
python3 -c "import secrets; print('PROD:', secrets.token_urlsafe(64))"
```

### **Separate Databases**

- Development: Can be reset, cleared, filled with test data
- Production: Real user data, regular backups, never reset

### **API Keys**

- Development: Test/sandbox API keys (Circle, Nodit)
- Production: Production API keys with rate limits

---

## 🚀 Quick Setup Commands

### **1. Set Up Branches**

```bash
cd /home/davey/Documents/rowell/dev/preklo

# Create and push development branch
git checkout -b development
git push -u origin development

# Create .github/workflows directory for CI/CD (optional)
mkdir -p .github/workflows
```

### **2. Deploy Development Environment**

```bash
# Railway Backend (Dev)
# - Go to railway.app
# - New Project → Import from GitHub
# - Select repository
# - Select `development` branch
# - Add environment variables
# - Add custom domain: api-dev.preklo.rowellholdings.co.za

# Vercel Frontend (Dev)
# - Go to vercel.com
# - New Project → Import from GitHub
# - Select repository
# - Production Branch: development
# - Add environment variables
# - Add custom domain: dev.preklo.rowellholdings.co.za
```

### **3. Deploy Production Environment**

```bash
# Railway Backend (Prod)
# - Go to railway.app
# - New Project → Import from GitHub
# - Select repository
# - Select `main` branch
# - Add environment variables (production values)
# - Add custom domain: api.preklo.rowellholdings.co.za

# Vercel Frontend (Prod)
# - Go to vercel.com
# - New Project → Import from GitHub
# - Select repository
# - Production Branch: main
# - Add environment variables (production values)
# - Add custom domain: preklo.rowellholdings.co.za
```

---

## 📝 Configuration Files to Update

### **Update `frontend/.env.local`**

Create environment-specific files:

```bash
# .env.development
VITE_API_BASE_URL=https://api-dev.preklo.rowellholdings.co.za
VITE_APP_NAME=Preklo (Development)
VITE_APP_VERSION=1.0.0-dev
VITE_ENVIRONMENT=development

# .env.production
VITE_API_BASE_URL=https://api.preklo.rowellholdings.co.za
VITE_APP_NAME=Preklo
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=production
```

### **Update CORS in `backend/app/main.py`**

```python
# Add environment-specific CORS
from .config import settings

if settings.debug:
    # Development - allow all
    allow_origins = ["*"]
else:
    # Production - specific domains only
    allow_origins = [
        "https://preklo.rowellholdings.co.za",
        "https://dev.preklo.rowellholdings.co.za",
        "http://localhost:8080",  # For local development
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ✅ Deployment Checklist

### **Pre-Deployment**

- [ ] Branches created: `main` and `development`
- [ ] Branch protection rules set up on GitHub
- [ ] DNS records configured for custom domains
- [ ] Separate JWT secrets generated
- [ ] Environment variables prepared for both environments

### **Development Deployment**

- [ ] Railway project created for backend (dev)
- [ ] Vercel project created for frontend (dev)
- [ ] Custom domains configured
- [ ] Environment variables set
- [ ] Test deployment successful
- [ ] Can access: dev.preklo.rowellholdings.co.za

### **Production Deployment**

- [ ] Railway project created for backend (prod)
- [ ] Vercel project created for frontend (prod)
- [ ] Custom domains configured
- [ ] Environment variables set (production values)
- [ ] Test deployment successful
- [ ] Can access: preklo.rowellholdings.co.za

### **Post-Deployment**

- [ ] All features tested on development
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Security review passed
- [ ] Ready for public testing

---

## 🎯 Benefits of This Setup

1. **Safety**: Test on dev before deploying to production
2. **Professional**: Proper git workflow and environments
3. **Custom Domain**: Your own branded domain
4. **Rollback**: Easy to revert if something breaks
5. **Parallel Development**: Multiple features can be developed simultaneously
6. **CI/CD**: Automatic deployments on merge
7. **Different Configurations**: Separate secrets and settings per environment

---

## 🚦 Current Status vs Target

### **Current (ngrok)**
- ❌ Temporary URL
- ❌ Computer must stay on
- ❌ Not professional for testing
- ❌ No environment separation

### **Target (Custom Domain + Branches)**
- ✅ Professional domain: preklo.rowellholdings.co.za
- ✅ Always available
- ✅ Separate dev and prod environments
- ✅ Proper git workflow
- ✅ Auto-deployment
- ✅ Ready for hackathon submission

---

## ⏱️ Time Estimate

- **Git Setup**: 15 minutes
- **DNS Configuration**: 15-30 minutes (depends on DNS propagation)
- **Railway Dev Deployment**: 45 minutes
- **Vercel Dev Deployment**: 30 minutes
- **Railway Prod Deployment**: 45 minutes
- **Vercel Prod Deployment**: 30 minutes
- **Testing & Verification**: 30 minutes

**Total**: ~3-4 hours

---

## 🎯 Next Steps

1. **Now**: Set up git branches
2. **Next**: Configure DNS for custom domains
3. **Then**: Deploy development environment first
4. **Test**: Verify everything works on dev
5. **Finally**: Deploy production environment
6. **Launch**: Share preklo.rowellholdings.co.za with testers!

---

**Ready to start?** Let's begin with setting up the git branches!


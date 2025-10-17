# Preklo Public Testing Guide

**Created**: October 17, 2025  
**Status**: Pre-Public Release Checklist

---

## 🎯 Can You Go Public Now?

**Short Answer**: Not yet - you need to deploy first!

**Current Status**: 
- ✅ App works locally on your machine
- ❌ Not accessible to the public (localhost only)
- ❌ Not deployed to production servers

---

## 🚀 Two Options to Make It Public

### **Option 1: Quick & Temporary (30 min - 1 hour)**

**Use Tunneling for Immediate Testing**

#### Using ngrok (Recommended for quick testing):

```bash
# Install ngrok
# Download from: https://ngrok.com/download
# Or: sudo apt install ngrok (Linux)

# Terminal 1: Start your backend
cd /home/davey/Documents/rowell/dev/preklo
source venv/bin/activate
cd backend
./start.sh

# Terminal 2: Expose backend
ngrok http 8000
# Copy the URL (e.g., https://abc123.ngrok.io)

# Terminal 3: Update frontend .env
cd /home/davey/Documents/rowell/dev/preklo/frontend
# Edit .env.local:
VITE_API_BASE_URL=https://abc123.ngrok.io

# Terminal 3: Start frontend
npm run dev

# Terminal 4: Expose frontend
ngrok http 8080
# Copy the URL (e.g., https://xyz789.ngrok.io)

# Share the frontend URL with testers!
```

**Pros:**
- ✅ Fast (30 minutes to set up)
- ✅ No deployment needed
- ✅ Good for quick feedback

**Cons:**
- ⚠️ URLs change every time you restart
- ⚠️ Free tier has hourly limits
- ⚠️ Your computer must stay on
- ⚠️ Not professional for hackathon submission

---

### **Option 2: Professional Deployment (2-3 hours) - RECOMMENDED**

**Deploy to Production Servers**

#### Step 1: Deploy Backend to Railway (1-1.5 hours)

1. **Go to [railway.app](https://railway.app)**
   - Sign up/login with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your Preklo repository
   - Select the backend directory

3. **Add PostgreSQL Database**
   - Click "Add Service" → PostgreSQL
   - Railway auto-generates DATABASE_URL

4. **Set Environment Variables**
   - Go to your backend service → Variables
   - Add these (copy from your local .env):
   ```
   DATABASE_URL=${DATABASE_URL}  # Auto-provided by Railway
   JWT_SECRET_KEY=<generate new one>
   APTOS_NODE_URL=https://fullnode.testnet.aptoslabs.com/v1
   APTOS_PRIVATE_KEY=<your testnet private key>
   APTOS_CONTRACT_ADDRESS=0xa3bbeb9cc35bab4c3c0af22c9b1398e4d849d4b33ed59b59a6dc4b1ca5298a2d
   PROJECT_NAME=Preklo
   DEBUG=False
   API_V1_STR=/api/v1
   ```

5. **Deploy**
   - Railway auto-deploys on push
   - Wait for build to complete (5-10 minutes)
   - Note your backend URL: `https://preklo-backend-production.up.railway.app`

6. **Run Database Migrations**
   - In Railway console:
   ```bash
   alembic upgrade head
   ```

7. **Verify Health Check**
   ```bash
   curl https://your-backend-url.railway.app/health
   ```

#### Step 2: Deploy Frontend to Vercel (30-45 minutes)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend
cd /home/davey/Documents/rowell/dev/preklo/frontend

# Login to Vercel
vercel login

# Deploy
vercel --prod

# Follow prompts:
# - Set up and deploy? Yes
# - Scope? Your account
# - Link to existing project? No
# - Project name? preklo-frontend
# - Directory? ./
# - Override settings? No
```

**Then in Vercel Dashboard:**
1. Go to your project settings
2. Environment Variables
3. Add:
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   VITE_APP_NAME=Preklo
   VITE_APP_VERSION=1.0.0
   ```
4. Redeploy

**Your app is now live at**: `https://preklo-frontend.vercel.app`

---

## ✅ Pre-Public Testing Checklist

### **Security & Safety** (CRITICAL)

- [ ] **Verify no secrets in GitHub**
  ```bash
  # Check your repo for sensitive data
  grep -r "private_key" --exclude-dir=".git" --exclude-dir="venv"
  grep -r "secret_key" --exclude-dir=".git" --exclude-dir="venv"
  ```

- [ ] **Ensure .env is gitignored**
  ```bash
  cat .gitignore | grep .env
  # Should show: .env
  ```

- [ ] **Strong JWT Secret** (if deployed)
  ```bash
  # Generate a new one for production:
  python3 -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

- [ ] **Using Aptos Testnet** (not mainnet - no real money)
  - Check APTOS_NODE_URL points to testnet
  - Wallet uses testnet tokens only

- [ ] **Rate Limiting Active**
  - Already configured: 120 requests/minute
  - Test by making rapid requests

- [ ] **CORS Configured**
  - Currently set to `allow_origins=["*"]` 
  - Fine for testing, lock down for production

### **Functionality Testing**

- [ ] **Registration works**
  - Create new user
  - Verify email validation
  - Check username availability

- [ ] **Login works**
  - Login with credentials
  - JWT token generated
  - Session persists

- [ ] **Send money works**
  - Between two test accounts
  - Transaction appears on blockchain
  - Balance updates correctly

- [ ] **Payment requests work**
  - Create request
  - Generate QR code
  - Payment link accessible

- [ ] **Transaction history works**
  - Shows all transactions
  - Filters work
  - Search functions

### **Documentation for Testers**

- [ ] **Add Testing Instructions to README**
  ```markdown
  ## 🧪 Public Testing (Testnet Only)
  
  **Note**: This is a testnet deployment. No real money is involved.
  
  ### How to Test:
  1. Visit: https://your-frontend-url.vercel.app
  2. Register with any email (no verification needed)
  3. Your wallet is created automatically
  4. Request testnet tokens (instructions below)
  5. Send money to other testers!
  
  ### Get Testnet APT:
  - Use Aptos Faucet: https://aptoslabs.com/testnet-faucet
  - Enter your wallet address from Preklo profile
  
  ### Known Limitations:
  - Testnet only - no real money
  - May have occasional downtime
  - Data may be reset periodically
  
  ### Report Issues:
  - GitHub Issues: https://github.com/yourusername/preklo/issues
  - Include screenshots and steps to reproduce
  ```

- [ ] **Create TESTING.md Guide**
  - Step-by-step testing instructions
  - Common issues and solutions
  - How to get testnet tokens
  - How to report bugs

### **Monitoring & Support**

- [ ] **Set Up Error Monitoring**
  - Use Railway logs
  - Monitor error rates
  - Set up alerts for critical failures

- [ ] **Prepare for Support**
  - Discord/Telegram for testers?
  - GitHub Issues enabled?
  - Response plan for critical bugs?

---

## 📢 How to Announce Public Testing

### **Social Media Post Template**

```
🚀 Preklo Public Testing is LIVE! 

Send money globally using simple usernames - no wallet addresses needed!

✨ Try it now: https://preklo.vercel.app
📖 Docs: https://github.com/yourusername/preklo

⚠️ TESTNET ONLY - No real money involved

Built on @Aptos with Circle USDC
Send money as easy as texting!

#Aptos #DeFi #Payments #Web3 #CTRLMOVE
```

### **Where to Share**

1. **Twitter/X** - Tag @Aptos, use hackathon hashtags
2. **Discord** - Aptos community channels
3. **Reddit** - r/Aptos, r/cryptocurrency (be careful of rules)
4. **Telegram** - Aptos groups
5. **Your Network** - Friends, colleagues, crypto communities

### **What to Ask Testers**

1. How intuitive is the username system?
2. Did transactions complete successfully?
3. Any confusing parts of the UI?
4. Any bugs or errors encountered?
5. Would you use this for real transactions?

---

## 🐛 Handling Feedback

### **Bug Reports**
- Thank the tester
- Ask for reproduction steps
- Get screenshots/console logs
- Fix critical issues ASAP
- Update testers when fixed

### **Feature Requests**
- Thank them for input
- Add to backlog
- Explain if not feasible for MVP
- Prioritize based on frequency

### **Negative Feedback**
- Stay positive and professional
- Ask for specific pain points
- Use it to improve the product
- Show you're listening and acting

---

## ⚠️ Important Warnings for Testers

**Include these in your announcement:**

1. **Testnet Only**: No real money involved
2. **Beta Software**: Expect bugs and issues
3. **Data Not Permanent**: May be reset during testing
4. **No Support Guarantees**: Best effort support
5. **Use Test Data**: Don't use real emails/passwords you care about
6. **Privacy**: Assume all data is public for testing

---

## 📊 Success Metrics for Public Testing

Track these to measure success:

- [ ] Number of registered users
- [ ] Number of transactions completed
- [ ] Bug reports received
- [ ] Feature requests received  
- [ ] User feedback sentiment
- [ ] Transaction success rate
- [ ] Average session duration
- [ ] Return users

---

## 🎯 Recommended Timeline

### **Day 1-2: Deploy & Verify**
- Deploy to Railway + Vercel
- Test all features yourself
- Fix any deployment issues

### **Day 3-4: Private Beta**
- Share with 5-10 close friends/colleagues
- Get initial feedback
- Fix critical bugs

### **Day 5-7: Public Beta**
- Announce publicly
- Monitor closely
- Respond to feedback
- Fix issues as they arise

### **Day 8+: Iterate**
- Implement feedback
- Add requested features
- Prepare for hackathon submission

---

## 🚫 What NOT to Do

- ❌ Don't deploy with real mainnet funds
- ❌ Don't store user passwords in plain text (you're using bcrypt ✅)
- ❌ Don't ignore security warnings
- ❌ Don't promise features you can't deliver
- ❌ Don't leave debug mode on in production
- ❌ Don't expose private keys
- ❌ Don't share admin/test credentials publicly

---

## ✅ Ready to Go Public Checklist

**Before sharing publicly, verify:**

- [ ] ✅ Backend deployed and accessible
- [ ] ✅ Frontend deployed and accessible  
- [ ] ✅ Database configured and migrated
- [ ] ✅ All features tested and working
- [ ] ✅ No secrets in GitHub repository
- [ ] ✅ Using testnet only (no real money)
- [ ] ✅ Clear disclaimers in place
- [ ] ✅ Testing instructions written
- [ ] ✅ Support channels ready
- [ ] ✅ Error monitoring set up
- [ ] ⚠️ Rate limiting tested
- [ ] ⚠️ Backup plan if something breaks
- [ ] ⚠️ Time to monitor and respond

---

## 🎊 You're Ready When...

1. ✅ App is deployed and publicly accessible
2. ✅ All core features work end-to-end
3. ✅ No critical bugs in basic flows
4. ✅ Clear documentation for testers
5. ✅ You have time to monitor and respond
6. ✅ You're comfortable with the code being public

---

## 📝 Next Steps

**Right now, you should:**

1. **Choose your path**: Quick tunneling or proper deployment?
2. **If deploying**: Start with Railway backend (1.5 hours)
3. **Then**: Deploy Vercel frontend (30 minutes)
4. **Test everything** once deployed
5. **Create testing documentation**
6. **Soft launch** to friends first
7. **Then go public** with confidence!

---

**Need Help?** Check the main MVP_LAUNCH_CHECKLIST.md or QUICK_START.md for detailed deployment instructions!

**Ready to deploy?** Start with Railway backend - that's your critical path!


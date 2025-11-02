# 🧪 Quick Auth Testing Guide

## 🚀 Start Testing in 3 Steps

### Step 1: Start Backend
```bash
cd backend
source venv/bin/activate
python -m app.main
```

Backend should be running on `http://localhost:8000`

---

### Step 2: Start Mobile App
```bash
cd mobile
npm start
```

Then scan QR code with Expo Go on your iOS device.

---

### Step 3: Test Auth Flow

#### ✅ First Time User (Registration)
1. App opens → **Login screen** appears
2. Click **"Sign Up"**
3. Fill form:
   - Full Name: `John Doe`
   - Username: `johndoe` (without @)
   - Email: `john@example.com`
   - Password: `password123`
   - Confirm: `password123`
4. Click **"Create Account"**
5. ✨ **Success!** Auto-login → Dashboard appears

#### ✅ Returning User (Login)
1. Logout from Profile tab
2. **Login screen** appears
3. Enter:
   - Email: `john@example.com`
   - Password: `password123`
4. Click **"Sign In"**
5. ✨ **Success!** Dashboard appears

#### ✅ Persistent Auth
1. Login to app
2. **Close app completely**
3. Reopen app
4. ✨ **Still logged in!** Goes directly to Dashboard

#### ✅ Logout
1. Go to **Profile** tab
2. Scroll to bottom
3. Click **"Log Out"**
4. Confirm in alert
5. ✨ **Logged out!** Redirected to Login

---

## 📱 What You'll See

### Login Screen
```
┌─────────────────────┐
│                     │
│   [Preklo Logo]     │
│  Pay anyone instantly│
│                     │
│   Welcome back      │
│   Sign in to continue│
│                     │
│   Email             │
│   [email input]     │
│                     │
│   Password          │
│   [password input]  │
│                     │
│   Forgot password?  │
│                     │
│   [Sign In]         │
│                     │
│   Don't have account?│
│   Sign Up           │
│                     │
└─────────────────────┘
```

### Registration Screen
```
┌─────────────────────┐
│  ← Back             │
│                     │
│   [Preklo Logo]     │
│                     │
│   Create Account    │
│   Join Preklo...    │
│                     │
│   Full Name         │
│   [@username input] │
│   Email             │
│   Password          │
│   Confirm Password  │
│                     │
│   [Create Account]  │
│                     │
│   Already have account?│
│   Sign In           │
└─────────────────────┘
```

---

## 🎯 Expected Behavior

### ✅ On Registration Success:
- Loading spinner appears
- Success alert shown
- Auto-navigates to Dashboard
- Token saved to storage
- User data saved

### ✅ On Login Success:
- Loading spinner appears
- Navigates to Dashboard
- Token saved to storage
- User data saved
- Profile shows real username

### ✅ On Logout:
- Confirmation alert
- Token cleared
- User data cleared
- Redirects to Login

### ✅ On Token Expiry (401):
- Auto-logout triggered
- Token cleared
- Redirects to Login
- Alert shown (optional)

---

## 🐛 Common Issues & Fixes

### Issue: "Network Error"
**Symptom**: Login fails with network error

**Fix**:
1. Check backend is running: `curl http://localhost:8000/health`
2. For physical iOS device, update `constants/Config.ts`:
   ```typescript
   apiUrl: 'http://YOUR_IP:8000/api/v1'
   ```
   Find your IP: `ifconfig` (Mac) or `ipconfig` (Windows)

### Issue: "Login Failed - Invalid Credentials"
**Symptom**: Correct password but login fails

**Fix**:
1. Register new user first
2. Check backend logs for errors
3. Verify database is running

### Issue: App Stuck on White Screen
**Symptom**: App doesn't show login screen

**Fix**:
1. Check Expo logs for errors
2. Reload app: Shake device → Reload
3. Restart Expo dev server

### Issue: "User Not Found" on Login
**Symptom**: Just registered but can't login

**Fix**:
1. Check backend logs
2. Verify user created in database
3. Try registering with different email

---

## 📊 Backend Endpoints Being Called

### Registration Flow:
```
1. POST /api/v1/users
   Body: { username, email, password, full_name }
   Response: { success: true, data: { user } }

2. POST /api/v1/auth/login (auto-called)
   Body: username=email&password=password
   Response: { access_token, user }
```

### Login Flow:
```
POST /api/v1/auth/login
Body: username=email&password=password
Response: {
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "username": "johndoe",
    "email": "john@example.com",
    "wallet_address": "0x..."
  }
}
```

### Protected Requests (with auth):
```
GET /api/v1/users/profile
Headers: {
  "Authorization": "Bearer eyJ..."
}
```

---

## ✅ Test Checklist

Use this checklist to verify everything works:

- [ ] Backend is running on port 8000
- [ ] Mobile app starts and shows Login screen
- [ ] Can tap "Sign Up" to go to Register
- [ ] Can fill registration form
- [ ] Registration succeeds and auto-logs in
- [ ] Dashboard shows with bottom navigation
- [ ] Profile tab shows real username/email
- [ ] Can logout successfully
- [ ] Redirected to Login after logout
- [ ] Can login again with same credentials
- [ ] Login succeeds and goes to Dashboard
- [ ] Close and reopen app - still logged in
- [ ] Logout, close app, reopen - shows Login

---

## 🎉 Success Criteria

**Your auth integration is working if**:
1. ✅ Register → Auto-login → Dashboard
2. ✅ Login → Dashboard
3. ✅ Logout → Login screen
4. ✅ Close & reopen → Still logged in
5. ✅ Profile shows real user data
6. ✅ No errors in console/logs

---

## 📸 Screenshots Expected

### Login Screen
- Preklo logo at top
- Email and password inputs
- "Sign In" button
- "Sign Up" link at bottom

### Register Screen
- Back button at top
- Preklo logo
- 5 input fields
- "Create Account" button
- Terms text
- "Sign In" link

### Dashboard (After Auth)
- Balance cards
- Recent transactions
- Bottom navigation (5 tabs)
- All working!

### Profile (Logged In)
- Shows @username
- Shows email
- Shows wallet address
- "Log Out" button at bottom

---

## 🚀 You're Ready!

**Everything is set up**:
- ✅ Login screen with backend
- ✅ Registration screen with backend
- ✅ Auth service
- ✅ Token management
- ✅ Protected routes
- ✅ Logout functionality
- ✅ Persistent auth

**Just start testing!** 🎊

```bash
# Terminal 1
cd backend && python -m app.main

# Terminal 2
cd mobile && npm start
```

Then scan QR and start testing! 📱✨


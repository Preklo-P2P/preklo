# 🐛 Debug Setup - Backend Connection

## Current Configuration

✅ **Computer IP**: `192.168.8.4`  
✅ **Backend URL**: `http://192.168.8.4:8000/api/v1`  
✅ **Mobile Config**: Already set in `constants/Config.ts`

---

## 🔍 Quick Test

### 1. Test if Backend is Accessible from Your Phone

**On your phone's browser**, navigate to:
```
http://192.168.8.4:8000/docs
```

**Expected**: You should see the FastAPI Swagger docs

**If it doesn't load**:
- Check both devices are on same WiFi network
- Check firewall isn't blocking port 8000
- Try: `http://192.168.8.4:8000/health`

---

### 2. Test API Endpoint Directly

**From your computer terminal**:
```bash
# Test health endpoint
curl http://192.168.8.4:8000/health

# Should return:
# {"status":"healthy","database":"connected"}
```

---

### 3. Check Backend CORS Settings

The backend needs to allow requests from your mobile app.

**Check**: `backend/app/main.py` should have:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔧 Quick Fixes

### Fix 1: Update Backend CORS

If CORS is blocking requests:

```bash
cd backend/app
# Edit main.py and ensure CORS middleware is configured
```

### Fix 2: Test Network Connection

```bash
# From your phone, test if you can reach backend:
# Open Safari/Chrome on phone and go to:
http://192.168.8.4:8000/health
```

### Fix 3: Check Firewall

```bash
# On Linux, allow port 8000
sudo ufw allow 8000

# Or disable firewall temporarily for testing
sudo ufw disable
```

---

## 📱 Test Registration from Mobile

### Enable Debug Logging

I'll add console logs to see what's happening:

1. Open Expo app on your phone
2. Shake device to open Dev Menu
3. Click "Debug Remote JS"
4. Open Chrome DevTools to see logs
5. Try registering again
6. Check console for errors

---

## 🎯 Expected Network Flow

```
Mobile App (192.168.8.4:8081)
    ↓
    POST http://192.168.8.4:8000/api/v1/users
    ↓
Backend (192.168.8.4:8000)
    ↓
Returns: { success: true, data: {...} }
    ↓
Auto-login: POST /api/v1/auth/login
    ↓
Returns: { access_token: "...", user: {...} }
    ↓
Save to AsyncStorage
    ↓
Navigate to Dashboard
```

---

## ✅ Checklist

Test these in order:

- [ ] Backend running on port 8000
- [ ] Can access `http://192.168.8.4:8000/health` from computer
- [ ] Can access `http://192.168.8.4:8000/docs` from phone browser
- [ ] Both devices on same WiFi
- [ ] CORS enabled in backend
- [ ] Firewall allows port 8000
- [ ] Mobile app config has correct IP
- [ ] Try registration from mobile
- [ ] Check Expo logs for errors

---

## 🆘 If Still Not Working

**Run this test to see the actual error**:

In Expo Go app:
1. Shake device
2. "Debug Remote JS"
3. Open http://localhost:19000 or http://localhost:19001
4. Look at console when you try to register
5. Report the exact error message

Or tell me what happens when you click "Create Account" - do you see:
- Loading spinner?
- Error alert?
- Nothing at all?
- Something else?


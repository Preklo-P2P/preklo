# 📝 Configuration Notes

## 🌐 Backend API URL

**Current Configuration**: `http://192.168.8.4:8000/api/v1`

This is your computer's local IP address. The mobile app uses this to connect to your backend.

---

## 🔧 How to Find Your IP Address

### Mac/Linux:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Windows:
```bash
ipconfig
```

Look for your local network IP (usually starts with 192.168.x.x)

---

## 📱 Connection Types

### Physical iOS/Android Device (Current Setup ✅)
- **URL**: `http://192.168.8.4:8000/api/v1`
- **Why**: Device and computer must be on same WiFi network
- **File**: `constants/Config.ts`

### iOS Simulator (Mac only)
- **URL**: `http://localhost:8000/api/v1`
- **Why**: Simulator shares Mac's network
- **Change in**: `constants/Config.ts`

### Android Emulator
- **URL**: `http://10.0.2.2:8000/api/v1`
- **Why**: Special IP for host machine in Android emulator
- **Change in**: `constants/Config.ts`

---

## ✅ Current Setup

**Backend Running On**:
- Local: `http://localhost:8000`
- Network: `http://192.168.8.4:8000`

**Mobile App Connects To**:
- `http://192.168.8.4:8000/api/v1`

**Requirements**:
- ✅ Backend running
- ✅ Mobile device on same WiFi as computer
- ✅ Port 8000 accessible (no firewall blocking)

---

## 🧪 Test Connection

### 1. Verify Backend is Accessible
From your phone's browser, visit:
```
http://192.168.8.4:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. Test API from Mobile Browser
```
http://192.168.8.4:8000/docs
```

Should show FastAPI docs.

### 3. If Connection Fails

**Problem**: Can't reach backend from phone

**Solutions**:
1. Make sure phone and computer are on **same WiFi network**
2. Check firewall isn't blocking port 8000
3. Try disabling firewall temporarily
4. Verify backend is running: `curl http://localhost:8000/health`

---

## 🔄 Changing API URL

If you need to change the API URL:

**File**: `constants/Config.ts`

```typescript
const ENV = {
  dev: {
    apiUrl: 'http://YOUR_IP:8000/api/v1',  // ← Change this
    appName: 'Preklo (Dev)',
  },
```

After changing:
```bash
# Stop Expo (Ctrl+C)
# Restart
npm start
```

---

## 🐛 Debugging API Calls

Add this to see API requests in Expo logs:

**File**: `services/api.ts`

```typescript
// Add before export
api.interceptors.request.use((config) => {
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.log('API Error:', error.message, error.config?.url);
    return Promise.reject(error);
  }
);
```

Then check Expo logs when you try to register/login.

---

## ✅ Quick Checklist

Before testing registration:
- [ ] Backend running: `http://localhost:8000`
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] Phone on same WiFi as computer
- [ ] Config.ts has correct IP: `192.168.8.4`
- [ ] Expo app restarted after config change
- [ ] Check Expo logs for API requests

---

**Your IP**: `192.168.8.4` ✅ (Already configured!)

**Ready to test!** Try registering a new user and watch the Expo logs for API requests.


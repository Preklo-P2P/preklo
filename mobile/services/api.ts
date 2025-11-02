import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Config from '../constants/Config';

const api = axios.create({
  baseURL: Config.apiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  maxRedirects: 5, // Follow redirects
  validateStatus: (status) => status < 400, // Accept 2xx and 3xx
});

// Add request logging for debugging
api.interceptors.request.use(
  (config) => {
    console.log('🚀 API Request:', config.method?.toUpperCase(), config.url);
    console.log('📍 Full URL:', config.baseURL + config.url);
    if (config.data) {
      const dataStr = typeof config.data === 'string' ? config.data : JSON.stringify(config.data);
      console.log('📦 Data:', dataStr.substring(0, 100));
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('preklo_auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 Added auth token to request');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config?.url || 'unknown');
    if (response.data) {
      const dataStr = typeof response.data === 'string' ? response.data : JSON.stringify(response.data);
      console.log('📥 Response data:', dataStr.substring(0, 150));
    }
    return response;
  },
  async (error) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      console.error('❌ API Error:', error.response.status, error.response.statusText);
      console.error('📍 URL:', error.config?.url || 'unknown');
      console.error('📝 Response:', error.response.data);
      
      if (error.response.status === 401) {
        // Handle unauthorized - clear token and redirect to login
        await AsyncStorage.removeItem('preklo_auth_token');
        await AsyncStorage.removeItem('preklo_user_data');
        console.log('🚪 Cleared auth token due to 401');
      }
    } else if (error.request) {
      // Request was made but no response received (network error)
      console.error('❌ Network Error: No response received');
      console.error('📍 URL:', error.config?.url || 'unknown');
      console.error('💡 Check your internet connection or backend server');
    } else {
      // Something else happened
      console.error('❌ Request Setup Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

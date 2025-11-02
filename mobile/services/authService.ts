import AsyncStorage from '@react-native-async-storage/async-storage';
import api from './api';

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
}

interface AuthResponse {
  success: boolean;
  data: {
    access_token: string;
    token_type: string;
    user: {
      id: string;
      username: string;
      email: string;
      full_name: string;
      wallet_address: string;
    };
  };
  message?: string;
}

const AUTH_TOKEN_KEY = 'preklo_auth_token';
const USER_DATA_KEY = 'preklo_user_data';

class AuthService {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      console.log('🔐 Attempting login for:', credentials.email);
      console.log('📡 Making login request to:', api.defaults.baseURL + '/auth/login');

      const response = await api.post('/auth/login', {
        username: credentials.email,
        password: credentials.password,
      });

      console.log('✅ Login response:', response.data);

      // Backend returns: { status, message, data: { user, tokens } }
      const tokens = response.data.data?.tokens;
      const user = response.data.data?.user;

      if (tokens?.access_token && user) {
        await this.saveAuthData(tokens.access_token, user);
        console.log('💾 Auth data saved successfully');
        
        return {
          success: true,
          data: {
            access_token: tokens.access_token,
            token_type: tokens.token_type,
            user: user,
          },
        };
      }

      return {
        success: false,
        data: null as any,
        message: 'Invalid response from server',
      };
    } catch (error: any) {
      console.error('❌ Login error:', error.message);
      console.error('❌ Error details:', error.response?.data);
      return {
        success: false,
        data: null as any,
        message: error.response?.data?.detail || 'Login failed. Please try again.',
      };
    }
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    try {
      console.log('📝 Attempting registration for:', data.email);
      console.log('📡 API Base URL:', api.defaults.baseURL);
      console.log('📤 Registration data:', {
        username: data.username.replace('@', ''),
        email: data.email,
        full_name: data.full_name,
      });

      const response = await api.post('/auth/register-simple', {
        username: data.username.replace('@', ''),
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        terms_agreed: true,
      });

      console.log('✅ Registration response:', response.data);

      // After registration, save user data and return success
      // User can login manually on next screen
      if (response.data.success || response.data.data) {
        const userData = response.data.data;
        
        // Try auto-login but don't fail registration if login fails
        try {
          console.log('🔄 Auto-logging in after registration...');
          const loginResult = await this.login({
            email: data.email,
            password: data.password,
          });
          
          if (loginResult.success) {
            return loginResult;
          }
        } catch (loginError) {
          console.error('⚠️ Auto-login failed, but registration succeeded');
          console.error('User can login manually');
        }
        
        // Return success even if auto-login failed
        return {
          success: true,
          data: response.data,
          message: 'Account created! Please login to continue.',
        };
      }

      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      console.error('❌ Registration error:', error.message);
      console.error('❌ Error details:', error.response?.data);
      console.error('❌ Full error:', error);
      return {
        success: false,
        data: null as any,
        message: error.response?.data?.detail || error.message || 'Registration failed. Please try again.',
      };
    }
  }

  async saveAuthData(token: string, user: any) {
    try {
      await AsyncStorage.setItem(AUTH_TOKEN_KEY, token);
      await AsyncStorage.setItem(USER_DATA_KEY, JSON.stringify(user));
    } catch (error) {
      console.error('Failed to save auth data:', error);
    }
  }

  async getAuthToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(AUTH_TOKEN_KEY);
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  async getUserData(): Promise<any | null> {
    try {
      const userData = await AsyncStorage.getItem(USER_DATA_KEY);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to get user data:', error);
      return null;
    }
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getAuthToken();
    return !!token;
  }

  async logout() {
    try {
      await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
      await AsyncStorage.removeItem(USER_DATA_KEY);
    } catch (error) {
      console.error('Failed to logout:', error);
    }
  }
}

export default new AuthService();


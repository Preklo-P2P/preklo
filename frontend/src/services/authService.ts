import { api, apiConfig } from '@/config/api';

// Types
export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  terms_agreed: boolean;
}

export interface LoginData {
  username: string;
  password: string;
  remember_me: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  wallet_address: string;
  full_name?: string;
  is_custodial: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiResponse<T> {
  status: string;
  message: string;
  data: T;
}

// Auth Service
export const authService = {
  // Register a new user
  async register(data: RegisterData): Promise<AuthResponse> {
    try {
      console.log('Registration data being sent:', data);
      const response = await api.post<ApiResponse<any>>(
        apiConfig.endpoints.register,
        data
      );
      
      if (response.status === 'success') {
        // Store user data (no token for registration, user needs to login)
        localStorage.setItem('preklo_username', response.data.username);
        localStorage.setItem('preklo_email', response.data.email);
        localStorage.setItem('preklo_wallet_address', response.data.wallet_address);
        localStorage.setItem('preklo_user_id', response.data.id);
        
        // Return mock auth response for now (user will need to login)
        return {
          access_token: '', // No token on registration
          token_type: 'bearer',
          user: {
            id: response.data.id,
            username: response.data.username,
            email: response.data.email,
            wallet_address: response.data.wallet_address,
            full_name: response.data.full_name,
            is_custodial: response.data.is_custodial,
            is_active: response.data.is_active,
            created_at: response.data.created_at,
          }
        };
      } else {
        throw new Error(response.message || 'Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  // Login user
  async login(data: LoginData): Promise<AuthResponse> {
    try {
      const response = await api.post<ApiResponse<any>>(
        apiConfig.endpoints.login,
        data
      );
      
      if (response.status === 'success') {
        // Extract tokens and user data from nested structure
        const tokens = response.data.tokens;
        const user = response.data.user;
        
        // Store token and user data
        localStorage.setItem('preklo_access_token', tokens.access_token);
        localStorage.setItem('preklo_username', user.username);
        localStorage.setItem('preklo_email', user.email);
        localStorage.setItem('preklo_wallet_address', user.wallet_address);
        localStorage.setItem('preklo_user_id', user.id);
        
        return {
          access_token: tokens.access_token,
          token_type: tokens.token_type,
          user: user
        };
      } else {
        throw new Error(response.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  // Logout user
  async logout(): Promise<void> {
    try {
      await api.post(apiConfig.endpoints.logout);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of API call success
      localStorage.removeItem('preklo_access_token');
      localStorage.removeItem('preklo_refresh_token');
      localStorage.removeItem('preklo_username');
      localStorage.removeItem('preklo_email');
      localStorage.removeItem('preklo_wallet_address');
      localStorage.removeItem('preklo_user_id');
    }
  },

  // Get current user
  async getCurrentUser(): Promise<User> {
    try {
      const response = await api.get<ApiResponse<User>>(
        `${apiConfig.endpoints.user}/me`
      );
      
      if (response.status === 'success') {
        return response.data;
      } else {
        throw new Error(response.message || 'Failed to get user data');
      }
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    const token = localStorage.getItem('preklo_access_token');
    const username = localStorage.getItem('preklo_username');
    
    if (!token || !username) {
      return false;
    }
    
    // Check if token is expired by decoding the JWT
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      if (payload.exp && payload.exp < currentTime) {
        // Token is expired, clear it
        this.logout();
        return false;
      }
      
      return true;
    } catch (error) {
      // Invalid token format, clear it
      this.logout();
      return false;
    }
  },

  // Get stored user data
  getStoredUserData(): Partial<User> | null {
    const username = localStorage.getItem('preklo_username');
    const email = localStorage.getItem('preklo_email');
    const walletAddress = localStorage.getItem('preklo_wallet_address');
    const userId = localStorage.getItem('preklo_user_id');

    if (username && email) {
      return {
        id: userId || '',
        username,
        email,
        wallet_address: walletAddress || '',
      };
    }

    return null;
  },
};

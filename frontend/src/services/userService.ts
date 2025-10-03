import { api, apiConfig } from '@/config/api';

// Types
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

export interface Balance {
  currency: string;
  balance: number;
}

export interface ApiResponse<T> {
  status: string;
  message: string;
  data: T;
}

// User Service
export const userService = {
  // Get current user profile
  async getCurrentUser(): Promise<User> {
    try {
      // Get user ID from localStorage (set during login)
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found. Please login again.');
      }
      
      const response = await api.get<User>(
        `${apiConfig.endpoints.user}/${userId}`
      );
      
      // The user endpoint returns the user data directly, not wrapped in a response object
      return response;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },

  // Get user balance
  async getBalance(): Promise<Balance[]> {
    try {
      const response = await api.get<any>(
        apiConfig.endpoints.balance
      );
      
      if (response.success) {
        // Convert the backend format to frontend format
        const balances = response.data.balances;
        const result = [
          { currency: 'APT', balance: parseFloat(balances.APT) },
          { currency: 'USDC', balance: parseFloat(balances.USDC) }
        ];
        return result;
      } else {
        throw new Error(response.message || 'Failed to get balance');
      }
    } catch (error) {
      console.error('Get balance error:', error);
      throw error;
    }
  },

  // Update user profile
  async updateProfile(data: Partial<User>): Promise<User> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.put<User>(
        `${apiConfig.endpoints.user}/${userId}`,
        data
      );
      
      // The user API returns the user data directly
      return response;
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  },

  // Get user transactions
  async getTransactions(limit: number = 50, offset: number = 0): Promise<any[]> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.get<any[]>(
        `${apiConfig.endpoints.transactions}/user/${userId}/history?limit=${limit}&offset=${offset}`
      );
      
      // The transactions API returns the data directly
      return response;
    } catch (error) {
      console.error('Get transactions error:', error);
      throw error;
    }
  },
};

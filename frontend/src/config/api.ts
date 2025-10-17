// API Configuration
// Set VITE_API_BASE_URL in your .env.local file or environment
// For local development: VITE_API_BASE_URL=http://localhost:8000
// For production: VITE_API_BASE_URL=https://your-backend-url.railway.app
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiConfig = {
  baseURL: API_BASE_URL,
  endpoints: {
    // Auth endpoints
    register: '/api/v1/auth/register-simple',
    login: '/api/v1/auth/login',
    logout: '/api/v1/auth/logout',
    
    // User endpoints
    user: '/api/v1/users',
    userProfile: '/api/v1/users/profile',
    
    // Wallet endpoints
    wallet: '/api/v1/wallet',
    balance: '/api/v1/wallet/balance',
    
    // Transaction endpoints
    transactions: '/api/v1/transactions',
    
    // Username endpoints
    username: '/api/v1/username',
    
    // Payment request endpoints
    payments: '/api/v1/payments',
    
    // Notification endpoints
    notifications: '/api/v1/notifications',
  }
};

// API helper functions
export const api = {
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${apiConfig.baseURL}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    // Add auth token if available
    const token = localStorage.getItem('preklo_access_token');
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
      console.log('Using token for request:', token.substring(0, 20) + '...');
    } else {
      console.log('No token found in localStorage');
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      console.log('Making API request to:', url);
      console.log('Request config:', config);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('API Error Response:', JSON.stringify(errorData, null, 2));
        
        // Handle 401 Unauthorized - token expired or invalid
        if (response.status === 401) {
          // Only logout if it's actually an authentication issue, not a transaction error
          const errorMessage = errorData.error?.message || errorData.detail || '';
          if (errorMessage.includes('Authentication') || errorMessage.includes('token') || errorMessage.includes('unauthorized')) {
            // Clear expired token and redirect to login
            localStorage.removeItem('preklo_access_token');
            localStorage.removeItem('preklo_refresh_token');
            localStorage.removeItem('preklo_username');
            localStorage.removeItem('preklo_email');
            localStorage.removeItem('preklo_wallet_address');
            localStorage.removeItem('preklo_user_id');
            
            // Redirect to login page
            window.location.href = '/landing#top';
            throw new Error('Session expired. Please log in again.');
          }
          // If it's not an authentication error, just throw the original error
        }
        
        // Handle different error formats
        if (errorData.error && errorData.error.message) {
          throw new Error(errorData.error.message);
        } else if (errorData.error && errorData.error.details) {
          throw new Error(errorData.error.details.original_detail || errorData.error.message);
        } else if (errorData.detail) {
          throw new Error(errorData.detail);
        } else if (errorData.message) {
          throw new Error(errorData.message);
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  },

  // GET request
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  },

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  // DELETE request
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  },
};

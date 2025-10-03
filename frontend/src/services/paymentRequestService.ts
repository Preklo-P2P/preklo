import { api, apiConfig } from '@/config/api';

export interface PaymentRequest {
  id: string;
  payment_id: string;
  recipient_id: string;
  amount: number;
  currency_type: 'USDC' | 'APT';
  description?: string;
  qr_code_url?: string;
  payment_link?: string;
  status: 'pending' | 'paid' | 'expired' | 'cancelled';
  expiry_timestamp: string;
  created_at: string;
  updated_at?: string;
}

export interface PaymentRequestCreate {
  recipient_id: string;
  amount: number;
  currency_type: 'USDC' | 'APT';
  description?: string;
  expiry_hours?: number;
}

export interface PaymentRequestResponse {
  success: boolean;
  message: string;
  data: PaymentRequest;
}

export const paymentRequestService = {
  // Create a new payment request
  async createPaymentRequest(data: PaymentRequestCreate): Promise<PaymentRequestResponse> {
    try {
      const response = await api.post<PaymentRequestResponse>(
        `${apiConfig.endpoints.payments}/request`,
        data
      );
      return response;
    } catch (error) {
      console.error('Failed to create payment request:', error);
      throw error;
    }
  },

  // Get payment requests for current user
  async getUserPaymentRequests(
    status?: string,
    limit: number = 25,
    offset: number = 0
  ): Promise<PaymentRequest[]> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      let url = `${apiConfig.endpoints.payments}/user/${userId}/requests?limit=${limit}&offset=${offset}`;
      if (status) {
        url += `&status=${status}`;
      }

      const response = await api.get<PaymentRequest[]>(url);
      return response;
    } catch (error) {
      console.error('Failed to get payment requests:', error);
      throw error;
    }
  },

  // Get a specific payment request by ID
  async getPaymentRequest(paymentId: string): Promise<PaymentRequest> {
    try {
      const response = await api.get<PaymentRequest>(
        `${apiConfig.endpoints.payments}/request/${paymentId}`
      );
      return response;
    } catch (error) {
      console.error('Failed to get payment request:', error);
      throw error;
    }
  },

  // Cancel a payment request
  async cancelPaymentRequest(paymentId: string): Promise<{ success: boolean; message: string }> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.put<{ success: boolean; message: string }>(
        `${apiConfig.endpoints.payments}/request/${paymentId}/cancel`,
        { recipient_id: userId }
      );
      return response;
    } catch (error) {
      console.error('Failed to cancel payment request:', error);
      throw error;
    }
  },

  // Pay a payment request (this would trigger the send money flow)
  async payPaymentRequest(paymentId: string, payerPrivateKey: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post<{ success: boolean; message: string }>(
        `${apiConfig.endpoints.payments}/pay`,
        {
          payment_id: paymentId,
          payer_private_key: payerPrivateKey
        }
      );
      return response;
    } catch (error) {
      console.error('Failed to pay payment request:', error);
      throw error;
    }
  }
};

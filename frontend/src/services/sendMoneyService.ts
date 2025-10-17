import { api, apiConfig } from '@/config/api';

// Types
export interface SendMoneyRequest {
  recipient_username: string;
  amount: string;
  currency_type: 'APT' | 'USDC';
  password: string;
  description?: string;
}

export interface SendMoneyResponse {
  success: boolean;
  message: string;
  data: {
    transaction_hash: string;
    sender_address: string;
    recipient_address: string;
    recipient_username: string;
    amount: string;
    currency_type: string;
    status: string;
    description?: string;
    fee_amount: string;
    fee_percentage: string;
    fee_collected: boolean;
    created_at: string;
  };
}

export interface UserValidationResponse {
  username: string;
  available: boolean;
  suggested_usernames?: string[];
}

export interface Balance {
  currency: string;
  balance: number;
}

// Send Money Service
export const sendMoneyService = {
  // Validate if a username exists
  async validateUsername(username: string): Promise<boolean> {
    try {
      // Remove @ prefix if present
      const cleanUsername = username.startsWith('@') ? username.slice(1) : username;
      
      const response = await api.get<UserValidationResponse>(
        `${apiConfig.endpoints.username}/check/${cleanUsername}`
      );
      
      // If username is available, it means it doesn't exist (we want the opposite)
      return !response.available;
    } catch (error) {
      console.error('Username validation error:', error);
      return false;
    }
  },

  // Get user balance
  async getBalance(): Promise<Balance[]> {
    try {
      const response = await api.get<any>(apiConfig.endpoints.balance);
      
      if (response.success) {
        const balances = response.data.balances;
        return [
          { currency: 'APT', balance: parseFloat(balances.APT) },
          { currency: 'USDC', balance: parseFloat(balances.USDC) }
        ];
      } else {
        throw new Error(response.message || 'Failed to get balance');
      }
    } catch (error) {
      console.error('Get balance error:', error);
      throw error;
    }
  },

  // Send money using custodial wallet
  async sendMoneyCustodial(request: SendMoneyRequest): Promise<SendMoneyResponse> {
    try {

      const response = await api.post<SendMoneyResponse>(
        `${apiConfig.endpoints.transactions}/send-custodial`,
        request
      );

      if (response.success) {
        return response;
      } else {
        throw new Error(response.message || 'Failed to send money');
      }
    } catch (error) {
      console.error('Send money error (custodial):', error);
      throw error;
    }
  },

  // Send money using non-custodial wallet (Petra)
  async sendMoneyNonCustodial(request: Omit<SendMoneyRequest, 'password'>): Promise<SendMoneyResponse> {
    try {

      // Step 1: Call the Petra transaction preparation endpoint
      const response = await api.post<any>(
        `${apiConfig.endpoints.transactions}/send-petra`,
        {
          recipient_username: request.recipient_username,
          amount: request.amount,
          currency_type: request.currency_type,
          description: request.description
        }
      );

      if (!response.success) {
        throw new Error(response.message || 'Failed to prepare Petra transaction');
      }

      // Step 2: Get Petra wallet following documentation pattern
      const getAptosWallet = () => {
        if ('aptos' in window) {
          return (window as any).aptos;
        } else {
          // Open Petra installation page as per documentation
          window.open('https://petra.app/', '_blank');
          return null;
        }
      };

      const wallet = getAptosWallet();
      
      if (!wallet) {
        throw new Error('Petra wallet not found. Please install Petra wallet extension.');
      }

      // Step 3: Format recipient address properly for Aptos
      const formatAptosAddress = (address: string): string => {
        // Remove 0x prefix if present
        let cleanAddress = address.startsWith('0x') ? address.slice(2) : address;
        
        // Pad with zeros to make it 64 characters (32 bytes)
        cleanAddress = cleanAddress.padStart(64, '0');
        
        // Add 0x prefix back
        return `0x${cleanAddress}`;
      };

      const formattedRecipientAddress = formatAptosAddress(response.data.transaction_details.recipient_address);

      // Step 4: Create transaction payload for Petra wallet with proper gas configuration
      const transactionPayload = {
        type: "entry_function_payload",
        function: "0x1::coin::transfer",
        type_arguments: [request.currency_type === 'APT' ? "0x1::aptos_coin::AptosCoin" : "0x498d8926f16eb9ca90cab1b3a26aa6f97a080b3fcbe6e83ae150b7243a00fb68::usdc::USDC"],
        arguments: [
          formattedRecipientAddress,
          Math.floor(parseFloat(request.amount) * Math.pow(10, request.currency_type === 'APT' ? 8 : 6)).toString() // Convert to smallest unit (APT=8, USDC=6)
        ]
      };


      // Step 4: Sign and submit transaction with Petra wallet using new API format
      try {
        const txResult = await wallet.signAndSubmitTransaction({ payload: transactionPayload });

        // Step 5: Confirm transaction with backend to save to database
        try {
          const confirmResponse = await api.post<any>(
            `${apiConfig.endpoints.transactions}/confirm-petra`,
            {
              transaction_hash: txResult.hash,
              recipient_username: request.recipient_username,
              amount: request.amount,
              currency_type: request.currency_type,
              description: request.description
            }
          );
        } catch (confirmError) {
          console.error('Failed to confirm transaction with backend:', confirmError);
          // Continue anyway - the transaction was successful on blockchain
        }

        // Step 6: Return success response with real transaction hash
        return {
          success: true,
          message: "Transaction sent successfully with Petra wallet",
          data: {
            transaction_hash: txResult.hash,
            sender_address: response.data.transaction_details.sender_address,
            recipient_address: response.data.transaction_details.recipient_address,
            recipient_username: response.data.transaction_details.recipient_username,
            amount: response.data.transaction_details.amount,
            currency_type: response.data.transaction_details.currency_type,
            status: "confirmed",
            description: response.data.transaction_details.description,
            fee_amount: response.data.transaction_details.fee_amount,
            fee_percentage: response.data.transaction_details.fee_percentage,
            fee_collected: false,
            created_at: new Date().toISOString(),
            petra_wallet_used: true
          }
        };

      } catch (petraError: any) {
        console.error('Petra wallet signing error:', petraError);
        
        // Handle specific Petra wallet errors as per documentation
        if (petraError.code === 4001) {
          throw new Error('Transaction cancelled by user');
        } else if (petraError.message && petraError.message.includes('MAX_GAS_UNITS_BELOW_MIN_TRANSACTION_GAS_UNITS')) {
          throw new Error('Insufficient gas limit. Please try again or contact support if the issue persists.');
        } else if (petraError.message && petraError.message.includes('insufficient')) {
          throw new Error('Insufficient funds to complete the transaction. Please check your balance.');
        } else if (petraError.message && petraError.message.includes('rejected')) {
          throw new Error('Transaction was rejected. Please try again.');
        }
        
        throw new Error(`Petra wallet error: ${petraError.message || 'Failed to sign transaction'}`);
      }

    } catch (error) {
      console.error('Send money error (non-custodial):', error);
      throw error;
    }
  },

  // Main send money function that detects wallet type
  async sendMoney(request: SendMoneyRequest, isCustodial: boolean): Promise<SendMoneyResponse> {
    if (isCustodial) {
      return this.sendMoneyCustodial(request);
    } else {
      return this.sendMoneyNonCustodial(request);
    }
  },

  // Get current user's wallet type
  async getCurrentUserWalletType(): Promise<{ isCustodial: boolean; walletAddress: string }> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found. Please login again.');
      }

      const response = await api.get<any>(`${apiConfig.endpoints.user}/${userId}`);
      
      // The user API returns the user data directly, not wrapped in status/data
      if (response && response.id) {
        return {
          isCustodial: response.is_custodial,
          walletAddress: response.wallet_address
        };
      } else {
        throw new Error('Failed to get user data');
      }
    } catch (error) {
      console.error('Get user wallet type error:', error);
      throw error;
    }
  },

  // Get transaction history
  async getTransactionHistory(limit: number = 50, offset: number = 0): Promise<any[]> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found. Please login again.');
      }

      const response = await api.get<any[]>(
        `${apiConfig.endpoints.transactions}/user/${userId}/history?limit=${limit}&offset=${offset}`
      );

      return response;
    } catch (error) {
      console.error('Get transaction history error:', error);
      throw error;
    }
  }
};

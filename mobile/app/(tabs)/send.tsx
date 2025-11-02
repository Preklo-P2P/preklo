import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import api from '../../services/api';
import authService from '../../services/authService';

type Step = 'recipient' | 'amount' | 'description' | 'confirm' | 'success';

export default function SendScreen() {
  const [currentStep, setCurrentStep] = useState<Step>('recipient');
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState<'USDC' | 'APT'>('USDC');
  const [description, setDescription] = useState('');
  const [password, setPassword] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isUserValid, setIsUserValid] = useState<boolean | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [txHash, setTxHash] = useState('');
  const [userId, setUserId] = useState('');
  const [userBalance, setUserBalance] = useState({ USDC: 0, APT: 0 });
  const [isLoadingBalance, setIsLoadingBalance] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const validationTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load user data and balance
  useEffect(() => {
    initializeData();
    
    // Cleanup timeout on unmount
    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, []);

  const initializeData = async () => {
    try {
      const userData = await authService.getUserData();
      if (userData?.id) {
        setUserId(userData.id);
        await fetchBalance(userData.id);
      }
    } catch (error) {
      console.error('Failed to initialize send screen:', error);
      setError('Failed to load user data');
    }
  };

  const fetchBalance = async (userIdParam: string) => {
    try {
      setIsLoadingBalance(true);
      const response = await api.get(`/users/${userIdParam}/balances`);
      
      if (response.data && Array.isArray(response.data)) {
        const balances: { [key: string]: number } = { USDC: 0, APT: 0 };
        response.data.forEach((balance: any) => {
          if (balance.currency_type === 'USDC') {
            balances.USDC = parseFloat(balance.balance || '0');
          } else if (balance.currency_type === 'APT') {
            balances.APT = parseFloat(balance.balance || '0');
          }
        });
        setUserBalance(balances);
      }
    } catch (error: any) {
      console.error('Failed to fetch balance:', error);
      setError('Failed to load balance');
    } finally {
      setIsLoadingBalance(false);
    }
  };

  // Real username validation using API
  const validateUsername = async (username: string) => {
    if (!username || username.length < 3) {
      setIsUserValid(null);
      return;
    }

    setIsValidating(true);
    setError(null);
    try {
      const response = await api.get(`/username/resolve/${username}`);
      if (response.data && response.data.username) {
        setIsUserValid(true);
      } else {
        setIsUserValid(false);
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        setIsUserValid(false);
      } else {
        console.error('Username validation error:', error);
        setError('Failed to validate username');
        setIsUserValid(false);
      }
    } finally {
      setIsValidating(false);
    }
  };

  const handleRecipientChange = (text: string) => {
    setRecipient(text);
    
    // Clear existing timeout
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }
    
    if (text.length >= 3) {
      // Debounce validation
      validationTimeoutRef.current = setTimeout(() => {
        validateUsername(text);
      }, 500);
    } else {
      setIsUserValid(null);
    }
  };

  const quickAmounts = [10, 25, 50, 100];

  // Helper function to normalize and parse amount (handles both comma and period as decimal separators)
  const parseAmount = (value: string): number => {
    if (!value || value.trim() === '') return 0;
    // Replace comma with period for parsing (handles European locale)
    const normalized = value.replace(',', '.');
    const parsed = parseFloat(normalized);
    return isNaN(parsed) ? 0 : parsed;
  };

  // Helper function to get parsed amount
  const getAmountValue = (): number => {
    return parseAmount(amount);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 'recipient':
        return recipient && isUserValid === true;
      case 'amount':
        const amountNum = getAmountValue();
        return amount.trim() !== '' && amountNum > 0 && amountNum <= userBalance[currency];
      case 'description':
        return true;
      case 'confirm':
        return password.length > 0;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep === 'recipient') setCurrentStep('amount');
    else if (currentStep === 'amount') setCurrentStep('description');
    else if (currentStep === 'description') setCurrentStep('confirm');
    else if (currentStep === 'confirm') handleSendMoney();
  };

  const handleBack = () => {
    if (currentStep === 'amount') {
      setCurrentStep('recipient');
    } else if (currentStep === 'description') {
      setCurrentStep('amount');
    } else if (currentStep === 'confirm') {
      setCurrentStep('description');
      setPassword('');
    } else if (currentStep === 'success') {
      router.back();
    } else {
      router.back();
    }
  };

  const handleSendMoney = async () => {
    if (!password) {
      Alert.alert('Password Required', 'Please enter your password to confirm the transaction');
      return;
    }

    setIsSending(true);
    setError(null);
    
    try {
      const amountValue = getAmountValue();
      if (amountValue <= 0) {
        Alert.alert('Invalid Amount', 'Amount must be greater than 0');
        setIsSending(false);
        return;
      }

      const response = await api.post('/transactions/send-custodial', {
        recipient_username: recipient,
        amount: amountValue.toString(),
        currency_type: currency,
        password: password,
        description: description || undefined,
      });

      if (response.data?.success !== false) {
        // Extract transaction hash from response
        const transactionHash = response.data?.data?.transaction_hash || 
                               response.data?.transaction_hash ||
                               response.data?.transaction_id || 
                               'Pending';
        
        setTxHash(transactionHash);
        setPassword('');
        setCurrentStep('success');
        
        // Refresh balance after successful send
        if (userId) {
          await fetchBalance(userId);
        }
      } else {
        throw new Error(response.data?.message || 'Transaction failed');
      }
    } catch (error: any) {
      console.error('Send money error:', error);
      
      let errorMessage = error.response?.data?.detail || 
                        error.response?.data?.message || 
                        error.response?.data?.error?.details?.original_detail ||
                        error.message || 
                        'Failed to send money. Please try again.';
      
      // Handle specific custodial wallet error
      if (errorMessage.includes('custodial wallet') || errorMessage.includes('custodial')) {
        errorMessage = 'Your account is not set up for custodial transactions. Please contact support or re-register your account.';
      }
      
      Alert.alert('Transaction Failed', errorMessage);
      setError(errorMessage);
    } finally {
      setIsSending(false);
    }
  };

  const getStepNumber = () => {
    const steps = { recipient: 1, amount: 2, description: 3, confirm: 4, success: 5 };
    return steps[currentStep];
  };

  const renderProgressBar = () => {
    if (currentStep === 'success') return null;
    const progress = (getStepNumber() / 4) * 100;
    return (
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>
        <Text style={styles.progressText}>Step {getStepNumber()} of 4</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Ionicons name="arrow-back" size={24} color="#374151" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>
          {currentStep === 'recipient' && 'Send to'}
          {currentStep === 'amount' && 'Enter amount'}
          {currentStep === 'description' && 'Add note'}
          {currentStep === 'confirm' && 'Confirm payment'}
          {currentStep === 'success' && 'Payment sent!'}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      {renderProgressBar()}

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {/* Step 1: Recipient */}
        {currentStep === 'recipient' && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepDescription}>Who are you sending money to?</Text>
            
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Recipient Username</Text>
              <View style={styles.inputWrapper}>
                <Text style={styles.atSymbol}>@</Text>
                <TextInput
                  style={styles.input}
                  placeholder="username"
                  value={recipient}
                  onChangeText={handleRecipientChange}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                {isValidating && <ActivityIndicator size="small" color="#10b981" />}
                {!isValidating && isUserValid === true && (
                  <Ionicons name="checkmark-circle" size={24} color="#10b981" />
                )}
                {!isValidating && isUserValid === false && (
                  <Ionicons name="close-circle" size={24} color="#ef4444" />
                )}
              </View>
              {isUserValid === false && (
                <Text style={styles.errorText}>User not found</Text>
              )}
              {isUserValid === true && (
                <Text style={styles.successText}>✓ User found</Text>
              )}
            </View>

            {error && (
              <View style={styles.errorContainer}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}
          </View>
        )}

        {/* Step 2: Amount */}
        {currentStep === 'amount' && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepDescription}>Sending to @{recipient}</Text>
            
            <View style={styles.amountContainer}>
              <View style={styles.amountInputRow}>
                {currency === 'USDC' && <Text style={styles.currencySymbol}>$</Text>}
                <TextInput
                  style={styles.amountInput}
                  placeholder="0.00"
                  value={amount}
                  onChangeText={(text) => {
                    // Remove any non-numeric characters except one decimal point or comma
                    let cleaned = text.replace(/[^0-9.,]/g, '');
                    
                    // If both comma and period exist, keep only the first one found
                    const hasComma = cleaned.includes(',');
                    const hasPeriod = cleaned.includes('.');
                    
                    if (hasComma && hasPeriod) {
                      // If both exist, use the first one and remove the other
                      const commaIndex = cleaned.indexOf(',');
                      const periodIndex = cleaned.indexOf('.');
                      
                      if (commaIndex < periodIndex) {
                        // Comma comes first, remove period
                        cleaned = cleaned.replace(/\./g, '');
                      } else {
                        // Period comes first, remove comma
                        cleaned = cleaned.replace(/,/g, '');
                      }
                    }
                    
                    // If multiple of the same separator, keep only the first one
                    const separator = cleaned.includes(',') ? ',' : '.';
                    const parts = cleaned.split(separator);
                    if (parts.length > 2) {
                      cleaned = parts[0] + separator + parts.slice(1).join('');
                    }
                    
                    setAmount(cleaned);
                  }}
                  keyboardType="decimal-pad"
                />
              </View>
              {amount.trim() !== '' && (
                <View style={{ marginTop: 8 }}>
                  {(() => {
                    const amountNum = getAmountValue();
                    if (amountNum <= 0) {
                      return <Text style={styles.errorText}>Amount must be greater than 0</Text>;
                    } else if (amountNum > userBalance[currency]) {
                      return <Text style={styles.errorText}>Insufficient balance</Text>;
                    } else {
                      return null;
                    }
                  })()}
                </View>
              )}
              
              <View style={styles.currencyToggle}>
                <TouchableOpacity
                  style={[styles.currencyButton, currency === 'USDC' && styles.currencyButtonActive]}
                  onPress={() => setCurrency('USDC')}
                >
                  <Text style={[styles.currencyButtonText, currency === 'USDC' && styles.currencyButtonTextActive]}>
                    USDC
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.currencyButton, currency === 'APT' && styles.currencyButtonActive]}
                  onPress={() => setCurrency('APT')}
                >
                  <Text style={[styles.currencyButtonText, currency === 'APT' && styles.currencyButtonTextActive]}>
                    APT
                  </Text>
                </TouchableOpacity>
              </View>

              {isLoadingBalance ? (
                <ActivityIndicator size="small" color="#10b981" style={{ marginTop: 8 }} />
              ) : (
                <Text style={styles.balanceText}>
                  Balance: {currency === 'USDC' ? '$' : ''}{userBalance[currency].toFixed(2)} {currency}
                </Text>
              )}
            </View>

            <View style={styles.quickAmountsContainer}>
              <Text style={styles.quickAmountsLabel}>Quick amounts:</Text>
              <View style={styles.quickAmountsRow}>
                {quickAmounts.map((amt) => (
                  <TouchableOpacity
                    key={amt}
                    style={styles.quickAmountButton}
                    onPress={() => setAmount(amt.toString())}
                  >
                    <Text style={styles.quickAmountText}>${amt}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>
        )}

        {/* Step 3: Description */}
        {currentStep === 'description' && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepDescription}>
              Sending {currency === 'USDC' ? '$' : ''}{getAmountValue().toFixed(2)} {currency} to @{recipient}
            </Text>
            
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Add a note (optional)</Text>
              <TextInput
                style={styles.descriptionInput}
                placeholder="What's this payment for?"
                value={description}
                onChangeText={setDescription}
                multiline
                maxLength={100}
              />
              <Text style={styles.characterCount}>{description.length}/100</Text>
            </View>

            <View style={styles.suggestionsContainer}>
              <Text style={styles.suggestionsLabel}>Common:</Text>
              {['Lunch', 'Rent', 'Gift', 'Services'].map((note) => (
                <TouchableOpacity
                  key={note}
                  style={styles.suggestionButton}
                  onPress={() => setDescription(note)}
                >
                  <Text style={styles.suggestionText}>{note}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Step 4: Confirm */}
        {currentStep === 'confirm' && (
          <View style={styles.stepContainer}>
            <View style={styles.confirmCard}>
              <View style={styles.recipientAvatar}>
                <Text style={styles.recipientAvatarText}>
                  {recipient.charAt(0).toUpperCase()}
                </Text>
              </View>
              
              <Text style={styles.confirmRecipient}>@{recipient}</Text>
              <Text style={styles.confirmAmount}>
                {currency === 'USDC' ? '$' : ''}{getAmountValue().toFixed(2)}
              </Text>
              <Text style={styles.confirmCurrency}>{currency}</Text>

              {description && (
                <View style={styles.confirmNote}>
                  <Text style={styles.confirmNoteLabel}>Note:</Text>
                  <Text style={styles.confirmNoteText}>{description}</Text>
                </View>
              )}

              <View style={styles.confirmBreakdown}>
                <View style={styles.confirmRow}>
                  <Text style={styles.confirmLabel}>Amount</Text>
                  <Text style={styles.confirmValue}>
                    {currency === 'USDC' ? '$' : ''}{getAmountValue().toFixed(2)}
                  </Text>
                </View>
                <View style={styles.confirmRow}>
                  <Text style={styles.confirmLabel}>Network fee</Text>
                  <Text style={styles.confirmValue}>
                    {currency === 'USDC' ? '$' : ''}~0.01
                  </Text>
                </View>
                <View style={[styles.confirmRow, styles.confirmTotal]}>
                  <Text style={styles.confirmTotalLabel}>Total</Text>
                  <Text style={styles.confirmTotalValue}>
                    {currency === 'USDC' ? '$' : ''}{(getAmountValue() + 0.01).toFixed(2)}
                  </Text>
                </View>
              </View>

              <View style={styles.passwordContainer}>
                <Text style={styles.inputLabel}>Enter your password to confirm</Text>
                <TextInput
                  style={styles.passwordInput}
                  placeholder="Password"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              {error && (
                <View style={styles.errorContainer}>
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Step 5: Success */}
        {currentStep === 'success' && (
          <View style={styles.successContainer}>
            <View style={styles.successIcon}>
              <Ionicons name="checkmark-circle" size={80} color="#10b981" />
            </View>
            
            <Text style={styles.successTitle}>Payment Sent!</Text>
            <Text style={styles.successSubtitle}>
              {currency === 'USDC' ? '$' : ''}{getAmountValue().toFixed(2)} {currency} sent to @{recipient}
            </Text>

            <View style={styles.successCard}>
              <View style={styles.successRow}>
                <Text style={styles.successLabel}>Transaction ID</Text>
                <TouchableOpacity>
                  <Ionicons name="copy-outline" size={20} color="#6b7280" />
                </TouchableOpacity>
              </View>
              <Text style={styles.successHash}>{txHash}</Text>
              
              <View style={styles.successRow}>
                <Text style={styles.successLabel}>Status</Text>
                <View style={styles.successBadge}>
                  <Ionicons name="checkmark-circle" size={16} color="#10b981" />
                  <Text style={styles.successBadgeText}>Confirmed</Text>
                </View>
              </View>
            </View>

            <TouchableOpacity
              style={styles.successButton}
              onPress={() => router.push('/')}
            >
              <Text style={styles.successButtonText}>Back to Home</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>

      {/* Action Button */}
      {currentStep !== 'success' && (
        <View style={styles.footer}>
          <TouchableOpacity
            style={[styles.actionButton, !canProceed() && styles.actionButtonDisabled]}
            onPress={handleNext}
            disabled={!canProceed() || isSending}
          >
            {isSending ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <>
                <Text style={styles.actionButtonText}>
                  {currentStep === 'confirm' ? 'Send Money' : 'Continue'}
                </Text>
                {currentStep === 'confirm' && (
                  <Ionicons name="send" size={20} color="#ffffff" style={{ marginLeft: 8 }} />
                )}
              </>
            )}
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
  },
  progressContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#10b981',
  },
  progressText: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  stepContainer: {
    flex: 1,
  },
  stepDescription: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 24,
  },
  inputContainer: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  atSymbol: {
    fontSize: 18,
    color: '#10b981',
    marginRight: 4,
    fontWeight: '600',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
  },
  errorText: {
    fontSize: 12,
    color: '#ef4444',
    marginTop: 4,
  },
  successText: {
    fontSize: 12,
    color: '#10b981',
    marginTop: 4,
  },
  suggestionsContainer: {
    marginTop: 16,
  },
  suggestionsLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 8,
  },
  suggestionButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 8,
  },
  suggestionText: {
    fontSize: 14,
    color: '#374151',
  },
  amountContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  amountInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  currencySymbol: {
    fontSize: 32,
    color: '#6b7280',
    marginRight: 8,
  },
  amountInput: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#374151',
    minWidth: 150,
  },
  currencyToggle: {
    flexDirection: 'row',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 4,
    marginBottom: 12,
  },
  currencyButton: {
    paddingVertical: 8,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  currencyButtonActive: {
    backgroundColor: '#10b981',
  },
  currencyButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  currencyButtonTextActive: {
    color: '#ffffff',
  },
  balanceText: {
    fontSize: 14,
    color: '#6b7280',
  },
  quickAmountsContainer: {
    marginTop: 16,
  },
  quickAmountsLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 8,
  },
  quickAmountsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  quickAmountButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  quickAmountText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  descriptionInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#374151',
    minHeight: 100,
    textAlignVertical: 'top',
  },
  characterCount: {
    fontSize: 12,
    color: '#6b7280',
    textAlign: 'right',
    marginTop: 4,
  },
  confirmCard: {
    backgroundColor: '#f9fafb',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
  },
  recipientAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#10b981',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  recipientAvatarText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  confirmRecipient: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  confirmAmount: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 4,
  },
  confirmCurrency: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 16,
  },
  confirmNote: {
    width: '100%',
    padding: 12,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    marginBottom: 16,
  },
  confirmNoteLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  confirmNoteText: {
    fontSize: 14,
    color: '#374151',
  },
  confirmBreakdown: {
    width: '100%',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  confirmRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  confirmLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  confirmValue: {
    fontSize: 14,
    color: '#374151',
  },
  confirmTotal: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  confirmTotalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  confirmTotalValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  successContainer: {
    alignItems: 'center',
    paddingTop: 40,
  },
  successIcon: {
    marginBottom: 24,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  successSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  successCard: {
    width: '100%',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  successRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  successLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  successHash: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: '#374151',
    marginBottom: 16,
  },
  successBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  successBadgeText: {
    fontSize: 12,
    color: '#10b981',
    fontWeight: '500',
  },
  successButton: {
    backgroundColor: '#10b981',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  successButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  footer: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  actionButton: {
    backgroundColor: '#10b981',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    minHeight: 56,
  },
  actionButtonDisabled: {
    backgroundColor: '#e5e7eb',
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  passwordContainer: {
    width: '100%',
    marginTop: 24,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  passwordInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#374151',
    marginTop: 8,
  },
  errorContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#fef2f2',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#fecaca',
  },
});

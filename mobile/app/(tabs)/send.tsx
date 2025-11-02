import React, { useState } from 'react';
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

type Step = 'recipient' | 'amount' | 'description' | 'confirm' | 'success';

export default function SendScreen() {
  const [currentStep, setCurrentStep] = useState<Step>('recipient');
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState<'USDC' | 'APT'>('USDC');
  const [description, setDescription] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isUserValid, setIsUserValid] = useState<boolean | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [txHash, setTxHash] = useState('');

  const userBalance = { USDC: 1234.56, APT: 45.32 };

  // Mock username validation
  const validateUsername = (username: string) => {
    setIsValidating(true);
    setTimeout(() => {
      setIsUserValid(username.length > 3);
      setIsValidating(false);
    }, 500);
  };

  const handleRecipientChange = (text: string) => {
    setRecipient(text);
    if (text.length > 3) {
      validateUsername(text);
    } else {
      setIsUserValid(null);
    }
  };

  const quickAmounts = [10, 25, 50, 100];

  const canProceed = () => {
    switch (currentStep) {
      case 'recipient':
        return recipient && isUserValid;
      case 'amount':
        return amount && parseFloat(amount) > 0 && parseFloat(amount) <= userBalance[currency];
      case 'description':
        return true;
      case 'confirm':
        return true;
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
    if (currentStep === 'amount') setCurrentStep('recipient');
    else if (currentStep === 'description') setCurrentStep('amount');
    else if (currentStep === 'confirm') setCurrentStep('description');
    else if (currentStep === 'success') router.back();
    else router.back();
  };

  const handleSendMoney = () => {
    setIsSending(true);
    // Mock API call
    setTimeout(() => {
      setTxHash('0x' + Math.random().toString(16).substr(2, 40));
      setIsSending(false);
      setCurrentStep('success');
    }, 2000);
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

            <View style={styles.suggestionsContainer}>
              <Text style={styles.suggestionsLabel}>Recent:</Text>
              {['john_doe', 'maria_garcia', 'alex_smith'].map((name) => (
                <TouchableOpacity
                  key={name}
                  style={styles.suggestionButton}
                  onPress={() => {
                    setRecipient(name);
                    setIsUserValid(true);
                  }}
                >
                  <Text style={styles.suggestionText}>@{name}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Step 2: Amount */}
        {currentStep === 'amount' && (
          <View style={styles.stepContainer}>
            <Text style={styles.stepDescription}>Sending to @{recipient}</Text>
            
            <View style={styles.amountContainer}>
              <View style={styles.amountInputRow}>
                <Text style={styles.currencySymbol}>$</Text>
                <TextInput
                  style={styles.amountInput}
                  placeholder="0.00"
                  value={amount}
                  onChangeText={setAmount}
                  keyboardType="decimal-pad"
                />
              </View>
              
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

              <Text style={styles.balanceText}>
                Balance: ${userBalance[currency].toFixed(2)} {currency}
              </Text>
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
              Sending ${amount} {currency} to @{recipient}
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
              <Text style={styles.confirmAmount}>${parseFloat(amount).toFixed(2)}</Text>
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
                  <Text style={styles.confirmValue}>${amount}</Text>
                </View>
                <View style={styles.confirmRow}>
                  <Text style={styles.confirmLabel}>Network fee</Text>
                  <Text style={styles.confirmValue}>$0.01</Text>
                </View>
                <View style={[styles.confirmRow, styles.confirmTotal]}>
                  <Text style={styles.confirmTotalLabel}>Total</Text>
                  <Text style={styles.confirmTotalValue}>
                    ${(parseFloat(amount) + 0.01).toFixed(2)}
                  </Text>
                </View>
              </View>
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
              ${amount} {currency} sent to @{recipient}
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
});

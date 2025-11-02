import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Share,
  Alert,
  Clipboard,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import QRCode from 'react-native-qrcode-svg';
import api from '../../services/api';
import authService from '../../services/authService';

type Tab = 'qr' | 'request';

interface UserData {
  id: string;
  username: string;
  email: string;
  full_name: string;
  wallet_address: string;
}

export default function ReceiveScreen() {
  const [activeTab, setActiveTab] = useState<Tab>('qr');
  const [requestAmount, setRequestAmount] = useState('');
  const [requestDescription, setRequestDescription] = useState('');
  const [requestFrom, setRequestFrom] = useState('');
  const [username, setUsername] = useState('');
  const [userId, setUserId] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingRequest, setIsCreatingRequest] = useState(false);
  const [createdPaymentRequest, setCreatedPaymentRequest] = useState<any>(null);

  const paymentLink = username ? `https://preklo.app/pay/${username}` : '';

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      setIsLoading(true);
      const userData = await authService.getUserData();
      if (userData) {
        setUsername(userData.username || '');
        setUserId(userData.id || '');
      }
    } catch (error) {
      console.error('❌ Error loading user data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleShare = async () => {
    if (!paymentLink) {
      Alert.alert('Error', 'Username not available');
      return;
    }
    try {
      await Share.share({
        message: `Send me money on Preklo! ${paymentLink}`,
        title: 'Send me money on Preklo',
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share payment link');
    }
  };

  const handleCopyLink = async () => {
    if (!paymentLink) {
      Alert.alert('Error', 'Payment link not available');
      return;
    }
    try {
      await Clipboard.setString(paymentLink);
      Alert.alert('Copied', 'Payment link copied to clipboard');
    } catch (error) {
      Alert.alert('Error', 'Failed to copy link');
    }
  };

  const handleCreateRequest = async () => {
    if (!requestAmount || parseFloat(requestAmount) <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    if (!userId) {
      Alert.alert('Error', 'User information not available. Please log in again.');
      return;
    }

    setIsCreatingRequest(true);
    try {
      const amount = parseFloat(requestAmount);
      const currencyType = 'USDC'; // Default to USDC for now
      
      console.log('📤 Creating payment request:', {
        recipient_id: userId,
        amount,
        currency_type: currencyType,
        description: requestDescription,
        expiry_hours: 24,
      });

      const response = await api.post('/payments/request', {
        recipient_id: userId,
        amount: amount.toString(),
        currency_type: currencyType,
        description: requestDescription || undefined,
        expiry_hours: 24,
      });

      console.log('✅ Payment request created:', response.data);

      if (response.data.success || response.data.data) {
        const paymentRequest = response.data.data || response.data;
        setCreatedPaymentRequest(paymentRequest);
        Alert.alert(
          'Request Created',
          `Payment request for $${requestAmount} ${currencyType} created successfully!`,
          [{ text: 'OK' }]
        );
        // Reset form
        setRequestAmount('');
        setRequestDescription('');
        setRequestFrom('');
      }
    } catch (error: any) {
      console.error('❌ Error creating payment request:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create payment request';
      Alert.alert('Error', errorMessage);
    } finally {
      setIsCreatingRequest(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Receive Money</Text>
        <Text style={styles.headerSubtitle}>@{username || 'loading...'}</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'qr' && styles.tabActive]}
          onPress={() => setActiveTab('qr')}
        >
          <Ionicons
            name="qr-code"
            size={20}
            color={activeTab === 'qr' ? '#10b981' : '#6b7280'}
          />
          <Text style={[styles.tabText, activeTab === 'qr' && styles.tabTextActive]}>
            QR Code
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'request' && styles.tabActive]}
          onPress={() => setActiveTab('request')}
        >
          <Ionicons
            name="cash-outline"
            size={20}
            color={activeTab === 'request' ? '#10b981' : '#6b7280'}
          />
          <Text style={[styles.tabText, activeTab === 'request' && styles.tabTextActive]}>
            Request
          </Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {/* QR Code Tab */}
        {activeTab === 'qr' && (
          <View style={styles.qrContainer}>
            {/* User Avatar */}
            {isLoading ? (
              <ActivityIndicator size="large" color="#10b981" />
            ) : (
              <>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>
                    {username ? username.charAt(0).toUpperCase() : '?'}
                  </Text>
                </View>
                <Text style={styles.usernameText}>@{username || 'loading...'}</Text>
                <Text style={styles.readyText}>Ready to receive payments</Text>

                {/* QR Code */}
                {username && paymentLink ? (
                  <View style={styles.qrCodeCard}>
                    <QRCode
                      value={paymentLink}
                      size={200}
                      color="#000000"
                      backgroundColor="#ffffff"
                    />
                    <Text style={styles.qrTitle}>Scan to Pay Me</Text>
                    <Text style={styles.qrSubtitle}>
                      Share this QR code to receive payments
                    </Text>
                  </View>
                ) : (
                  <View style={styles.qrCodeCard}>
                    <View style={styles.qrCodePlaceholder}>
                      <ActivityIndicator size="large" color="#10b981" />
                    </View>
                    <Text style={styles.qrTitle}>Loading QR Code...</Text>
                  </View>
                )}
              </>
            )}

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
                <Ionicons name="share-social" size={20} color="#10b981" />
                <Text style={styles.actionButtonText}>Share</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionButton}
                onPress={() => Alert.alert('Download', 'QR code download coming soon!')}
              >
                <Ionicons name="download" size={20} color="#10b981" />
                <Text style={styles.actionButtonText}>Download</Text>
              </TouchableOpacity>
            </View>

            {/* Payment Link */}
            <View style={styles.linkContainer}>
              <Text style={styles.linkLabel}>Payment Link</Text>
              <View style={styles.linkCard}>
                <Text style={styles.linkText} numberOfLines={1}>
                  {paymentLink}
                </Text>
                <TouchableOpacity onPress={handleCopyLink}>
                  <Ionicons name="copy-outline" size={20} color="#6b7280" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {/* Request Tab */}
        {activeTab === 'request' && (
          <View style={styles.requestContainer}>
            <Text style={styles.requestTitle}>Create Payment Request</Text>
            <Text style={styles.requestSubtitle}>
              Request a specific amount from someone
            </Text>

            {/* Request From */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Request from (optional)</Text>
              <View style={styles.inputWrapper}>
                <Text style={styles.atSymbol}>@</Text>
                <TextInput
                  style={styles.input}
                  placeholder="username"
                  value={requestFrom}
                  onChangeText={setRequestFrom}
                  autoCapitalize="none"
                />
              </View>
            </View>

            {/* Amount */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Amount</Text>
              <View style={styles.amountInputWrapper}>
                <Text style={styles.dollarSign}>$</Text>
                <TextInput
                  style={styles.amountInput}
                  placeholder="0.00"
                  value={requestAmount}
                  onChangeText={setRequestAmount}
                  keyboardType="decimal-pad"
                />
                <View style={styles.currencyBadge}>
                  <Text style={styles.currencyBadgeText}>USDC</Text>
                </View>
              </View>
            </View>

            {/* Description */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Description</Text>
              <TextInput
                style={styles.descriptionInput}
                placeholder="What's this request for?"
                value={requestDescription}
                onChangeText={setRequestDescription}
                multiline
                maxLength={100}
              />
              <Text style={styles.characterCount}>{requestDescription.length}/100</Text>
            </View>

            {/* Expiry Info */}
            <View style={styles.infoCard}>
              <Ionicons name="time-outline" size={20} color="#6b7280" />
              <Text style={styles.infoText}>Request will expire in 24 hours</Text>
            </View>

            {/* Create Button */}
            <TouchableOpacity
              style={[styles.createButton, isCreatingRequest && styles.createButtonDisabled]}
              onPress={handleCreateRequest}
              disabled={isCreatingRequest}
            >
              {isCreatingRequest ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={styles.createButtonText}>Create Request</Text>
              )}
            </TouchableOpacity>

            {/* Show Created Payment Request Info */}
            {createdPaymentRequest && (
              <View style={styles.infoCard}>
                <Ionicons name="checkmark-circle" size={20} color="#10b981" />
                <View style={styles.requestInfo}>
                  <Text style={styles.requestInfoTitle}>Request Created!</Text>
                  <Text style={styles.requestInfoText}>
                    Share this link: {createdPaymentRequest.payment_link}
                  </Text>
                  <TouchableOpacity
                    style={styles.copyRequestLink}
                    onPress={() => {
                      if (createdPaymentRequest.payment_link) {
                        Clipboard.setString(createdPaymentRequest.payment_link);
                        Alert.alert('Copied', 'Payment request link copied!');
                      }
                    }}
                  >
                    <Text style={styles.copyRequestLinkText}>Copy Link</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {/* Recent Requests */}
            <View style={styles.recentSection}>
              <Text style={styles.recentTitle}>Recent Requests</Text>
              <View style={styles.emptyState}>
                <Ionicons name="document-text-outline" size={48} color="#d1d5db" />
                <Text style={styles.emptyText}>No payment requests yet</Text>
                <Text style={styles.emptySubtext}>
                  Create your first payment request above
                </Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  tabContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 8,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 8,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    minHeight: 44,
  },
  tabActive: {
    backgroundColor: '#10b98110',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  tabTextActive: {
    color: '#10b981',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  qrContainer: {
    alignItems: 'center',
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#10b981',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  avatarText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  usernameText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  readyText: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 32,
  },
  qrCodeCard: {
    width: '100%',
    backgroundColor: '#f9fafb',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
  },
  qrCodePlaceholder: {
    width: 200,
    height: 200,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#e5e7eb',
  },
  qrTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  qrSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  actionButtons: {
    flexDirection: 'row',
    width: '100%',
    gap: 12,
    marginBottom: 24,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    minHeight: 44,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  linkContainer: {
    width: '100%',
  },
  linkLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  linkCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  linkText: {
    flex: 1,
    fontSize: 14,
    color: '#6b7280',
    fontFamily: 'monospace',
  },
  requestContainer: {
    flex: 1,
  },
  requestTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  requestSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 20,
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
    minHeight: 44,
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
  amountInputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    minHeight: 44,
  },
  dollarSign: {
    fontSize: 20,
    color: '#6b7280',
    marginRight: 4,
  },
  amountInput: {
    flex: 1,
    fontSize: 24,
    fontWeight: '600',
    color: '#374151',
  },
  currencyBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: '#10b98110',
    borderRadius: 6,
  },
  currencyBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#10b981',
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
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 24,
  },
  infoText: {
    fontSize: 14,
    color: '#6b7280',
  },
  createButton: {
    backgroundColor: '#10b981',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 32,
    minHeight: 56,
    justifyContent: 'center',
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  recentSection: {
    marginTop: 16,
  },
  recentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 16,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
    marginTop: 12,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
  },
  createButtonDisabled: {
    opacity: 0.6,
  },
  requestInfo: {
    flex: 1,
    marginLeft: 12,
  },
  requestInfoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#10b981',
    marginBottom: 4,
  },
  requestInfoText: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  copyRequestLink: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#10b981',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  copyRequestLinkText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
});

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import api from '../../services/api';
import authService from '../../services/authService';

interface Transaction {
  id: string;
  type: 'sent' | 'received';
  username: string;
  amount: number;
  currency: string;
  status: string;
  timestamp: string;
  description?: string;
}

export default function DashboardScreen() {
  // User state
  const [username, setUsername] = useState('');
  const [userId, setUserId] = useState('');
  
  // Balance state
  const [usdcBalance, setUsdcBalance] = useState(0);
  const [aptBalance, setAptBalance] = useState(0);
  
  // Transactions state
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  
  // Loading states
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [isLoadingBalance, setIsLoadingBalance] = useState(true);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Error state
  const [error, setError] = useState<string | null>(null);

  // Load user data from AsyncStorage
  const loadUserData = async () => {
    try {
      const userData = await authService.getUserData();
      if (userData) {
        console.log('📱 Loaded user data:', userData);
        setUsername(userData.username);
        setUserId(userData.id);
        return userData;
      } else {
        console.log('❌ No user data found in AsyncStorage');
        setError('Please login again');
      }
    } catch (error) {
      console.error('❌ Error loading user data:', error);
      setError('Failed to load user data');
    } finally {
      setIsLoadingUser(false);
    }
    return null;
  };

  // Fetch user balance from backend
  const fetchBalance = async (userId: string) => {
    try {
      console.log('💰 Fetching balance for user:', userId);
      
      const response = await api.get(`/users/${userId}/balances`);
      console.log('✅ Balance response:', response.data);
      
      if (response.data && Array.isArray(response.data)) {
        // Find USDC balance
        const usdcBalanceData = response.data.find((b: any) => b.currency_type === 'USDC');
        if (usdcBalanceData) {
          setUsdcBalance(parseFloat(usdcBalanceData.balance || usdcBalanceData.available_balance || 0));
        }
        
        // Find APT balance
        const aptBalanceData = response.data.find((b: any) => b.currency_type === 'APT');
        if (aptBalanceData) {
          setAptBalance(parseFloat(aptBalanceData.balance || aptBalanceData.available_balance || 0));
        }
        
        console.log('💵 USDC Balance:', usdcBalanceData?.balance || 0);
        console.log('💵 APT Balance:', aptBalanceData?.balance || 0);
      }
    } catch (error: any) {
      console.error('❌ Error fetching balance:', error);
      console.error('❌ Error details:', error.response?.data);
      setError('Failed to load balance');
    } finally {
      setIsLoadingBalance(false);
    }
  };

  // Format timestamp to relative time (e.g., "2h ago")
  const formatTimestamp = (timestamp: string | Date) => {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Fetch transaction history from backend
  const fetchTransactions = async (userId: string) => {
    try {
      console.log('📜 Fetching transactions for user:', userId);
      
      // Use the enhanced history endpoint which uses current authenticated user
      const response = await api.get(`/transactions/history?limit=5`);
      
      console.log('✅ Transactions response:', response.data);
      
      // Enhanced history endpoint returns { transactions: [], pagination: {} }
      const transactionsArray = response.data?.transactions || (Array.isArray(response.data) ? response.data : []);
      
      if (transactionsArray && Array.isArray(transactionsArray)) {
        // Transform backend data to match our UI format
        const formattedTransactions: Transaction[] = transactionsArray.map((tx: any) => {
          const isSent = tx.sender_id === userId;
          const otherUser = isSent ? tx.recipient : tx.sender;
          
          return {
            id: tx.id || tx.transaction_hash,
            type: isSent ? 'sent' : 'received',
            username: otherUser?.username ? `@${otherUser.username}` : 'Unknown',
            amount: parseFloat(tx.amount || 0),
            currency: tx.currency_type || 'USDC',
            status: tx.status || 'confirmed',
            timestamp: formatTimestamp(tx.created_at),
            description: tx.description
          };
        });
        
        setTransactions(formattedTransactions);
        console.log('📊 Formatted transactions:', formattedTransactions.length);
      }
    } catch (error: any) {
      console.error('❌ Error fetching transactions:', error);
      console.error('❌ Error details:', error.response?.data);
      // Don't show error for transactions - just leave empty
    } finally {
      setIsLoadingTransactions(false);
    }
  };

  // Load all data when component mounts
  useEffect(() => {
    initializeData();
  }, []);

  const initializeData = async () => {
    console.log('🚀 Initializing Dashboard data...');
    
    // First load user data from AsyncStorage
    const userData = await loadUserData();
    
    if (userData && userData.id) {
      // Then fetch balance and transactions from backend
      await Promise.all([
        fetchBalance(userData.id),
        fetchTransactions(userData.id)
      ]);
    }
    
    console.log('✅ Dashboard initialization complete');
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    console.log('🔄 Refreshing dashboard data...');
    
    try {
      const userData = await authService.getUserData();
      if (userData && userData.id) {
        await Promise.all([
          fetchBalance(userData.id),
          fetchTransactions(userData.id)
        ]);
      }
    } catch (error) {
      console.error('❌ Error refreshing:', error);
    }
    
    setRefreshing(false);
    console.log('✅ Refresh complete');
  }, []);

  // Show loading state
  if (isLoadingUser || isLoadingBalance) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
          <ActivityIndicator size="large" color="#10b981" />
          <Text style={{ marginTop: 16, color: '#6b7280' }}>Loading dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // Show error state
  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={[styles.container, { justifyContent: 'center', alignItems: 'center', padding: 32 }]}>
          <Ionicons name="alert-circle" size={64} color="#ef4444" />
          <Text style={{ marginTop: 16, fontSize: 18, fontWeight: '600', color: '#374151' }}>
            {error}
          </Text>
          <TouchableOpacity 
            style={{ marginTop: 24, paddingVertical: 12, paddingHorizontal: 24, backgroundColor: '#10b981', borderRadius: 8 }}
            onPress={initializeData}
          >
            <Text style={{ color: '#ffffff', fontWeight: '600' }}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.username}>@{username}</Text>
          <View style={styles.headerActions}>
            <TouchableOpacity style={styles.iconButton}>
              <Ionicons name="search" size={24} color="#374151" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.iconButton}>
              <Ionicons name="notifications" size={24} color="#374151" />
              <View style={styles.badge}>
                <Text style={styles.badgeText}>3</Text>
              </View>
            </TouchableOpacity>
          </View>
        </View>

        {/* Balance Card */}
        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Your Balance</Text>
          <View style={styles.balanceRow}>
            <Text style={styles.balanceAmount}>${usdcBalance.toFixed(2)}</Text>
            <Text style={styles.balanceCurrency}>USDC</Text>
          </View>
          <Text style={styles.secondaryBalance}>
            {aptBalance.toFixed(2)} APT
          </Text>
          <Text style={styles.refreshHint}>Pull to refresh</Text>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/send')}>
            <Ionicons name="arrow-forward-circle" size={32} color="#10b981" />
            <Text style={styles.actionText}>Send</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/receive')}>
            <Ionicons name="arrow-back-circle" size={32} color="#10b981" />
            <Text style={styles.actionText}>Receive</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={() => router.push('/history')}>
            <Ionicons name="bar-chart" size={32} color="#10b981" />
            <Text style={styles.actionText}>History</Text>
          </TouchableOpacity>
        </View>

        {/* Recent Activity */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Activity</Text>
            <TouchableOpacity onPress={() => router.push('/history')}>
              <Text style={styles.viewAll}>View All</Text>
            </TouchableOpacity>
          </View>

          {isLoadingTransactions ? (
            <View style={{ padding: 20, alignItems: 'center' }}>
              <ActivityIndicator size="small" color="#10b981" />
              <Text style={{ marginTop: 8, color: '#6b7280' }}>Loading transactions...</Text>
            </View>
          ) : transactions.length === 0 ? (
            <View style={{ padding: 40, alignItems: 'center' }}>
              <Ionicons name="receipt-outline" size={48} color="#d1d5db" />
              <Text style={{ marginTop: 16, fontSize: 16, color: '#6b7280' }}>No transactions yet</Text>
              <Text style={{ marginTop: 4, fontSize: 14, color: '#9ca3af' }}>Your transactions will appear here</Text>
            </View>
          ) : (
            transactions.map((tx) => (
            <TouchableOpacity key={tx.id} style={styles.transactionCard}>
              <View style={styles.transactionIcon}>
                <Ionicons
                  name={tx.type === 'sent' ? 'arrow-forward-circle' : 'arrow-back-circle'}
                  size={24}
                  color={tx.type === 'sent' ? '#f59e0b' : '#10b981'}
                />
              </View>
              <View style={styles.transactionContent}>
                <Text style={styles.transactionUsername}>{tx.username}</Text>
                <View style={styles.transactionMeta}>
                  <Ionicons
                    name={tx.status === 'confirmed' ? 'checkmark-circle' : 'time'}
                    size={14}
                    color={tx.status === 'confirmed' ? '#10b981' : '#f59e0b'}
                  />
                  <Text style={styles.transactionTime}>{tx.timestamp}</Text>
                </View>
              </View>
              <View style={styles.transactionAmount}>
                <Text
                  style={[
                    styles.amount,
                    tx.type === 'sent' ? styles.sentAmount : styles.receivedAmount,
                  ]}
                >
                  {tx.type === 'sent' ? '-' : '+'}${tx.amount.toFixed(2)}
                </Text>
                <Text style={styles.currency}>{tx.currency}</Text>
              </View>
            </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  username: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  iconButton: {
    padding: 8,
    position: 'relative',
  },
  badge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: '#ef4444',
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  balanceCard: {
    margin: 16,
    padding: 24,
    backgroundColor: '#f9fafb',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  balanceLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  balanceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
  },
  balanceAmount: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#374151',
  },
  balanceCurrency: {
    fontSize: 18,
    color: '#6b7280',
  },
  secondaryBalance: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 8,
  },
  refreshHint: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 12,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  actionButton: {
    alignItems: 'center',
    gap: 8,
    minWidth: 80,
    minHeight: 80,
    justifyContent: 'center',
  },
  actionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
  },
  viewAll: {
    fontSize: 14,
    fontWeight: '500',
    color: '#10b981',
  },
  transactionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  transactionIcon: {
    marginRight: 12,
  },
  transactionContent: {
    flex: 1,
  },
  transactionUsername: {
    fontSize: 16,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 4,
  },
  transactionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  transactionTime: {
    fontSize: 12,
    color: '#6b7280',
  },
  transactionAmount: {
    alignItems: 'flex-end',
  },
  amount: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  sentAmount: {
    color: '#f59e0b',
  },
  receivedAmount: {
    color: '#10b981',
  },
  currency: {
    fontSize: 12,
    color: '#6b7280',
  },
});


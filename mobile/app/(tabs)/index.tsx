import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';

// Mock data - replace with real API calls
const MOCK_USER = {
  username: '@your_username',
  usdcBalance: 1234.56,
  aptBalance: 45.32,
};

const MOCK_TRANSACTIONS = [
  {
    id: '1',
    type: 'sent',
    username: '@john_doe',
    amount: 25.00,
    currency: 'USDC',
    status: 'confirmed',
    timestamp: '2h ago',
    description: 'Lunch money',
  },
  {
    id: '2',
    type: 'received',
    username: '@maria_garcia',
    amount: 100.00,
    currency: 'USDC',
    status: 'confirmed',
    timestamp: '5h ago',
  },
  {
    id: '3',
    type: 'sent',
    username: '@alex_smith',
    amount: 50.00,
    currency: 'USDC',
    status: 'pending',
    timestamp: '1d ago',
    description: 'Rent split',
  },
];

export default function DashboardScreen() {
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    // Simulate API call
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  }, []);

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
          <Text style={styles.username}>{MOCK_USER.username}</Text>
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
            <Text style={styles.balanceAmount}>${MOCK_USER.usdcBalance.toFixed(2)}</Text>
            <Text style={styles.balanceCurrency}>USDC</Text>
          </View>
          <Text style={styles.secondaryBalance}>
            {MOCK_USER.aptBalance.toFixed(2)} APT
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

          {MOCK_TRANSACTIONS.map((tx) => (
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
          ))}
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


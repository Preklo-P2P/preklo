import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Modal,
  Share,
  RefreshControl,
  ActivityIndicator,
  Clipboard,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import authService from '../../services/authService';

interface Transaction {
  id: string;
  type: 'sent' | 'received';
  username: string;
  amount: number;
  currency: string;
  status: 'pending' | 'confirmed' | 'failed';
  timestamp: string;
  description?: string;
  date: string;
  txHash?: string;
  created_at?: string;
}

export default function HistoryScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<'all' | 'sent' | 'received'>('all');
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTransactions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const direction = filter === 'all' ? undefined : filter;
      const params: any = {
        limit: 100, // Load more for history screen
        offset: 0,
      };
      
      if (direction) {
        params.direction = direction;
      }

      console.log('📜 Fetching transaction history:', params);
      const response = await api.get('/transactions/history', { params });
      
      console.log('✅ Transactions response:', response.data);

      if (response.data && response.data.transactions) {
        const transactionsArray = response.data.transactions;
        
        // Transform API response to UI format
        const formattedTransactions: Transaction[] = transactionsArray.map((tx: any) => {
          const currentUserId = tx.sender?.id || tx.user_id;
          const isSent = tx.direction === 'sent' || (tx.sender && tx.sender.id === currentUserId);
          const otherUser = isSent ? tx.recipient : tx.sender;
          
          // Format date
          const date = formatDate(tx.created_at);
          const timestamp = formatTimestamp(tx.created_at);
          
          return {
            id: tx.id || tx.transaction_hash,
            type: isSent ? 'sent' : 'received',
            username: otherUser?.username ? `@${otherUser.username}` : (tx.recipient_address || tx.sender_address || 'Unknown'),
            amount: parseFloat(tx.amount || 0),
            currency: tx.currency_type || 'USDC',
            status: tx.status || 'confirmed',
            timestamp: timestamp,
            description: tx.description,
            date: date,
            txHash: tx.transaction_hash || tx.id,
            created_at: tx.created_at,
          };
        });
        
        setTransactions(formattedTransactions);
        console.log('📊 Formatted transactions:', formattedTransactions.length);
      } else {
        setTransactions([]);
      }
    } catch (error: any) {
      console.error('❌ Error fetching transactions:', error);
      console.error('❌ Error details:', error.response?.data);
      setError('Failed to load transactions');
      // Set empty array on error so UI shows empty state
      setTransactions([]);
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadTransactions();
    setRefreshing(false);
  }, [loadTransactions]);

  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'Unknown';
    
    try {
      const date = new Date(dateString);
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      
      // Reset time to compare dates only
      const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
      const yesterdayOnly = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
      
      if (dateOnly.getTime() === todayOnly.getTime()) {
        return 'Today';
      } else if (dateOnly.getTime() === yesterdayOnly.getTime()) {
        return 'Yesterday';
      } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      }
    } catch (e) {
      return 'Unknown';
    }
  };

  const formatTimestamp = (dateString?: string): string => {
    if (!dateString) return 'Unknown';
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays === 1) return '1d ago';
      if (diffDays < 7) return `${diffDays}d ago`;
      
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch (e) {
      return 'Unknown';
    }
  };

  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch = tx.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         tx.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filter === 'all' || tx.type === filter;
    return matchesSearch && matchesFilter;
  });

  // Group transactions by date
  const groupedTransactions = filteredTransactions.reduce((groups, tx) => {
    const date = tx.date;
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(tx);
    return groups;
  }, {} as Record<string, Transaction[]>);

  const getStatusIcon = (status: Transaction['status']) => {
    switch (status) {
      case 'confirmed':
        return <Ionicons name="checkmark-circle" size={16} color="#10b981" />;
      case 'pending':
        return <Ionicons name="time" size={16} color="#f59e0b" />;
      case 'failed':
        return <Ionicons name="close-circle" size={16} color="#ef4444" />;
    }
  };

  const getStatusText = (status: Transaction['status']) => {
    switch (status) {
      case 'confirmed':
        return 'Confirmed';
      case 'pending':
        return 'Pending';
      case 'failed':
        return 'Failed';
    }
  };

  const handleShare = async (tx: Transaction) => {
    try {
      await Share.share({
        message: `Payment ${tx.type === 'sent' ? 'to' : 'from'} ${tx.username}: $${tx.amount} ${tx.currency}\nTx: ${tx.txHash}`,
      });
    } catch (error) {
      console.error('Share failed:', error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Transaction History</Text>
      </View>

      {/* Search and Filter */}
      <View style={styles.searchContainer}>
        <View style={styles.searchWrapper}>
          <Ionicons name="search" size={20} color="#6b7280" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search transactions..."
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Ionicons name="close-circle" size={20} color="#6b7280" />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(!showFilters)}
        >
          <Ionicons name="filter" size={20} color="#374151" />
        </TouchableOpacity>
      </View>

      {/* Filter Options */}
      {showFilters && (
        <View style={styles.filtersContainer}>
          <TouchableOpacity
            style={[styles.filterChip, filter === 'all' && styles.filterChipActive]}
            onPress={() => setFilter('all')}
          >
            <Text style={[styles.filterChipText, filter === 'all' && styles.filterChipTextActive]}>
              All
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterChip, filter === 'sent' && styles.filterChipActive]}
            onPress={() => setFilter('sent')}
          >
            <Ionicons
              name="arrow-forward-circle"
              size={16}
              color={filter === 'sent' ? '#ffffff' : '#6b7280'}
            />
            <Text style={[styles.filterChipText, filter === 'sent' && styles.filterChipTextActive]}>
              Sent
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterChip, filter === 'received' && styles.filterChipActive]}
            onPress={() => setFilter('received')}
          >
            <Ionicons
              name="arrow-back-circle"
              size={16}
              color={filter === 'received' ? '#ffffff' : '#6b7280'}
            />
            <Text style={[styles.filterChipText, filter === 'received' && styles.filterChipTextActive]}>
              Received
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Transaction List */}
      {isLoading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#10b981" />
          <Text style={styles.loadingText}>Loading transactions...</Text>
        </View>
      ) : error && transactions.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="alert-circle-outline" size={64} color="#ef4444" />
          <Text style={styles.emptyText}>Failed to load transactions</Text>
          <Text style={styles.emptySubtext}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadTransactions}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView
          style={styles.content}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {Object.entries(groupedTransactions).map(([date, transactions]) => (
            <View key={date} style={styles.dateGroup}>
              <Text style={styles.dateHeader}>{date}</Text>
              {transactions.map((tx) => (
              <TouchableOpacity
                key={tx.id}
                style={styles.transactionCard}
                onPress={() => setSelectedTx(tx)}
              >
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
                    {getStatusIcon(tx.status)}
                    <Text style={styles.transactionTime}>{tx.timestamp}</Text>
                  </View>
                  {tx.description && (
                    <Text style={styles.transactionDescription}>{tx.description}</Text>
                  )}
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
        ))}

          {filteredTransactions.length === 0 && (
            <View style={styles.emptyState}>
              <Ionicons name="receipt-outline" size={64} color="#d1d5db" />
              <Text style={styles.emptyText}>No transactions found</Text>
              <Text style={styles.emptySubtext}>
                {searchQuery ? 'Try a different search' : 'Your transactions will appear here'}
              </Text>
            </View>
          )}
        </ScrollView>
      )}

      {/* Transaction Detail Modal */}
      <Modal
        visible={!!selectedTx}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedTx(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            {selectedTx && (
              <>
                <View style={styles.modalHeader}>
                  <Text style={styles.modalTitle}>Transaction Details</Text>
                  <TouchableOpacity onPress={() => setSelectedTx(null)}>
                    <Ionicons name="close" size={24} color="#374151" />
                  </TouchableOpacity>
                </View>

                <View style={styles.modalBody}>
                  <View style={styles.txAvatar}>
                    <Ionicons
                      name={selectedTx.type === 'sent' ? 'arrow-forward' : 'arrow-back'}
                      size={32}
                      color="#ffffff"
                    />
                  </View>

                  <Text style={styles.txUsername}>{selectedTx.username}</Text>
                  <Text style={styles.txAmount}>
                    {selectedTx.type === 'sent' ? '-' : '+'}${selectedTx.amount.toFixed(2)}
                  </Text>
                  <Text style={styles.txCurrency}>{selectedTx.currency}</Text>

                  {selectedTx.description && (
                    <View style={styles.txDescriptionCard}>
                      <Text style={styles.txDescriptionLabel}>Description</Text>
                      <Text style={styles.txDescriptionText}>{selectedTx.description}</Text>
                    </View>
                  )}

                  <View style={styles.txDetails}>
                    <View style={styles.txDetailRow}>
                      <Text style={styles.txDetailLabel}>Transaction ID</Text>
                      <TouchableOpacity
                        onPress={() => {
                          if (selectedTx.txHash) {
                            Clipboard.setString(selectedTx.txHash);
                            Alert.alert('Copied', 'Transaction hash copied to clipboard');
                          }
                        }}
                      >
                        <Ionicons name="copy-outline" size={20} color="#6b7280" />
                      </TouchableOpacity>
                    </View>
                    <Text style={styles.txHash}>{selectedTx.txHash || selectedTx.id}</Text>

                    <View style={styles.txDetailRow}>
                      <Text style={styles.txDetailLabel}>Status</Text>
                      <View style={styles.txStatus}>
                        {getStatusIcon(selectedTx.status)}
                        <Text style={styles.txStatusText}>{getStatusText(selectedTx.status)}</Text>
                      </View>
                    </View>

                    <View style={styles.txDetailRow}>
                      <Text style={styles.txDetailLabel}>Time</Text>
                      <Text style={styles.txDetailValue}>{selectedTx.timestamp}</Text>
                    </View>

                    <View style={styles.txDetailRow}>
                      <Text style={styles.txDetailLabel}>Network Fee</Text>
                      <Text style={styles.txDetailValue}>$0.01</Text>
                    </View>
                  </View>
                </View>

                <View style={styles.modalFooter}>
                  <TouchableOpacity
                    style={styles.modalButton}
                    onPress={() => handleShare(selectedTx)}
                  >
                    <Ionicons name="share-social" size={20} color="#10b981" />
                    <Text style={styles.modalButtonText}>Share</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.modalButton}
                    onPress={() => {
                      if (selectedTx.txHash) {
                        const explorerUrl = `https://explorer.aptoslabs.com/txn/${selectedTx.txHash}?network=testnet`;
                        Alert.alert(
                          'Open Explorer',
                          'Copy this URL to view on Aptos Explorer:\n' + explorerUrl,
                          [
                            {
                              text: 'Copy URL',
                              onPress: () => {
                                Clipboard.setString(explorerUrl);
                                Alert.alert('Copied', 'Explorer URL copied to clipboard');
                              },
                            },
                            { text: 'OK' },
                          ]
                        );
                      }
                    }}
                  >
                    <Ionicons name="open-outline" size={20} color="#10b981" />
                    <Text style={styles.modalButtonText}>View on Explorer</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
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
  searchContainer: {
    flexDirection: 'row',
    gap: 8,
    padding: 16,
  },
  searchWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    paddingHorizontal: 12,
    minHeight: 44,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
  },
  filterButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
  },
  filtersContainer: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  filterChipActive: {
    backgroundColor: '#10b981',
    borderColor: '#10b981',
  },
  filterChipText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  filterChipTextActive: {
    color: '#ffffff',
  },
  content: {
    flex: 1,
  },
  dateGroup: {
    marginBottom: 16,
  },
  dateHeader: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  transactionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    marginHorizontal: 16,
    marginBottom: 8,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
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
  transactionDescription: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
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
  emptyState: {
    alignItems: 'center',
    paddingVertical: 80,
    paddingHorizontal: 32,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6b7280',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingBottom: 32,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
  },
  modalBody: {
    padding: 24,
    alignItems: 'center',
  },
  txAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#10b981',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  txUsername: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  txAmount: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#374151',
  },
  txCurrency: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 16,
  },
  txDescriptionCard: {
    width: '100%',
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 16,
  },
  txDescriptionLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
  },
  txDescriptionText: {
    fontSize: 14,
    color: '#374151',
  },
  txDetails: {
    width: '100%',
  },
  txDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  txDetailLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  txHash: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: '#374151',
    marginBottom: 16,
  },
  txStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  txStatusText: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },
  txDetailValue: {
    fontSize: 14,
    color: '#374151',
  },
  modalFooter: {
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 24,
  },
  modalButton: {
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
  modalButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#10b981',
    borderRadius: 12,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
});

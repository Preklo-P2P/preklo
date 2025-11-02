import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function WalletConnectScreen() {
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnectPetra = async () => {
    setIsConnecting(true);
    
    // Simulate wallet connection
    setTimeout(() => {
      setIsConnecting(false);
      Alert.alert(
        'Coming Soon',
        'Petra Wallet integration is coming soon! For now, please use username/password login or create a custodial account.',
        [
          {
            text: 'Create Account',
            onPress: () => router.push('/register'),
          },
          {
            text: 'Login',
            onPress: () => router.push('/login'),
          },
        ]
      );
    }, 1000);
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Back Button */}
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color="#374151" />
        </TouchableOpacity>

        {/* Logo */}
        <View style={styles.logoContainer}>
          <Image
            source={require('../assets/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>

        {/* Header */}
        <View style={styles.headerContainer}>
          <Text style={styles.headerTitle}>Connect Your Wallet</Text>
          <Text style={styles.headerSubtitle}>
            Use your Petra wallet to access Preklo
          </Text>
        </View>

        {/* Wallet Connect Card */}
        <View style={styles.walletCard}>
          <View style={styles.walletIcon}>
            <Ionicons name="wallet" size={48} color="#10b981" />
          </View>
          
          <Text style={styles.walletTitle}>Petra Wallet</Text>
          <Text style={styles.walletDescription}>
            Connect your existing Petra wallet to send and receive payments
          </Text>

          {/* Connect Button */}
          <TouchableOpacity
            style={styles.connectButton}
            onPress={handleConnectPetra}
            disabled={isConnecting}
          >
            {isConnecting ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <>
                <Ionicons name="link" size={20} color="#ffffff" />
                <Text style={styles.connectButtonText}>Connect Petra Wallet</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Info Card */}
        <View style={styles.infoCard}>
          <Ionicons name="information-circle" size={20} color="#06b6d4" />
          <Text style={styles.infoText}>
            Don't have a wallet? Create a free custodial account instead.
          </Text>
        </View>

        {/* Alternative Option */}
        <TouchableOpacity
          style={styles.alternativeButton}
          onPress={() => router.push('/register')}
        >
          <Text style={styles.alternativeText}>Create Custodial Account Instead</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 20,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logo: {
    width: 100,
    height: 100,
  },
  headerContainer: {
    marginBottom: 32,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#6b7280',
  },
  walletCard: {
    backgroundColor: '#f9fafb',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  walletIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#10b98110',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  walletTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  walletDescription: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  connectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#10b981',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    minHeight: 56,
    width: '100%',
  },
  connectButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  infoCard: {
    flexDirection: 'row',
    gap: 12,
    padding: 16,
    backgroundColor: '#06b6d410',
    borderRadius: 12,
    marginBottom: 24,
  },
  infoText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
  },
  alternativeButton: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  alternativeText: {
    fontSize: 14,
    color: '#10b981',
    fontWeight: '600',
  },
});


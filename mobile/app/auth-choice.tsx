import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Image,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function AuthChoiceScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Image
            source={require('../assets/logo.png')}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.tagline}>Pay anyone, instantly</Text>
        </View>

        {/* Welcome Text */}
        <View style={styles.welcomeContainer}>
          <Text style={styles.welcomeTitle}>Welcome to Preklo</Text>
          <Text style={styles.welcomeSubtitle}>
            Choose how you'd like to get started
          </Text>
        </View>

        {/* Wallet Connection Option */}
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => router.push('/wallet-connect')}
        >
          <View style={styles.buttonContent}>
            <View style={styles.iconCircle}>
              <Ionicons name="wallet" size={24} color="#10b981" />
            </View>
            <View style={styles.buttonText}>
              <Text style={styles.buttonTitle}>Connect Wallet</Text>
              <Text style={styles.buttonSubtitle}>
                Use your existing Petra wallet
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#10b981" />
          </View>
        </TouchableOpacity>

        {/* Custodial Wallet Option */}
        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => router.push('/register')}
        >
          <View style={styles.buttonContent}>
            <View style={[styles.iconCircle, styles.iconCircleSecondary]}>
              <Ionicons name="shield-checkmark" size={24} color="#06b6d4" />
            </View>
            <View style={styles.buttonText}>
              <Text style={styles.buttonTitle}>Create Account</Text>
              <Text style={styles.buttonSubtitle}>
                We'll create a secure wallet for you
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#6b7280" />
          </View>
        </TouchableOpacity>

        {/* Divider */}
        <View style={styles.divider}>
          <View style={styles.dividerLine} />
          <Text style={styles.dividerText}>Already have an account?</Text>
          <View style={styles.dividerLine} />
        </View>

        {/* Login Link */}
        <TouchableOpacity
          style={styles.loginButton}
          onPress={() => router.push('/login')}
        >
          <Text style={styles.loginButtonText}>Sign In</Text>
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
    paddingVertical: 40,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logo: {
    width: 100,
    height: 100,
    marginBottom: 16,
  },
  appName: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 4,
  },
  tagline: {
    fontSize: 16,
    color: '#6b7280',
  },
  welcomeContainer: {
    marginBottom: 32,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#6b7280',
  },
  primaryButton: {
    backgroundColor: '#10b98110',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#10b981',
  },
  secondaryButton: {
    backgroundColor: '#f9fafb',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  iconCircleSecondary: {
    backgroundColor: '#06b6d410',
  },
  buttonText: {
    flex: 1,
  },
  buttonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  buttonSubtitle: {
    fontSize: 14,
    color: '#6b7280',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#e5e7eb',
  },
  dividerText: {
    marginHorizontal: 16,
    fontSize: 14,
    color: '#6b7280',
  },
  loginButton: {
    backgroundColor: '#f9fafb',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    minHeight: 56,
    justifyContent: 'center',
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
});


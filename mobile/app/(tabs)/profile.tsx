import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';

export default function ProfileScreen() {
  const [notificationsEnabled, setNotificationsEnabled] = React.useState(true);
  const [biometricsEnabled, setBiometricsEnabled] = React.useState(false);

  const username = '@your_username';
  const email = 'your.email@example.com';
  const walletAddress = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb';

  const handleLogout = () => {
    Alert.alert(
      'Log Out',
      'Are you sure you want to log out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Log Out',
          style: 'destructive',
          onPress: () => {
            // In real app, clear auth tokens and navigate to login
            Alert.alert('Logged Out', 'You have been logged out successfully');
          },
        },
      ]
    );
  };

  const SettingItem = ({
    icon,
    title,
    subtitle,
    onPress,
    showArrow = true,
    rightElement,
  }: {
    icon: keyof typeof Ionicons.glyphMap;
    title: string;
    subtitle?: string;
    onPress?: () => void;
    showArrow?: boolean;
    rightElement?: React.ReactNode;
  }) => (
    <TouchableOpacity
      style={styles.settingItem}
      onPress={onPress}
      disabled={!onPress && !rightElement}
    >
      <View style={styles.settingIconContainer}>
        <Ionicons name={icon} size={20} color="#10b981" />
      </View>
      <View style={styles.settingContent}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {rightElement}
      {showArrow && !rightElement && (
        <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
      )}
    </TouchableOpacity>
  );

  const SectionHeader = ({ title }: { title: string }) => (
    <Text style={styles.sectionHeader}>{title}</Text>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Profile & Settings</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* User Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {username.replace('@', '').charAt(0).toUpperCase()}
            </Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.username}>{username}</Text>
            <Text style={styles.email}>{email}</Text>
            <View style={styles.walletInfo}>
              <Ionicons name="wallet" size={14} color="#6b7280" />
              <Text style={styles.walletAddress}>
                {walletAddress.slice(0, 8)}...{walletAddress.slice(-6)}
              </Text>
              <TouchableOpacity
                onPress={() => Alert.alert('Copied', 'Wallet address copied to clipboard')}
              >
                <Ionicons name="copy-outline" size={14} color="#6b7280" />
              </TouchableOpacity>
            </View>
          </View>
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => Alert.alert('Edit Profile', 'Edit profile coming soon!')}
          >
            <Ionicons name="create-outline" size={20} color="#10b981" />
          </TouchableOpacity>
        </View>

        {/* Account Section */}
        <SectionHeader title="Account" />
        <View style={styles.section}>
          <SettingItem
            icon="person-outline"
            title="Username"
            subtitle={username}
            onPress={() => Alert.alert('Username', 'Username management coming soon!')}
          />
          <SettingItem
            icon="mail-outline"
            title="Email"
            subtitle={email}
            onPress={() => Alert.alert('Email', 'Email management coming soon!')}
          />
          <SettingItem
            icon="call-outline"
            title="Phone Number"
            subtitle="Not set"
            onPress={() => Alert.alert('Phone', 'Phone number management coming soon!')}
          />
          <SettingItem
            icon="shield-checkmark-outline"
            title="Verification"
            subtitle="Verified account"
            onPress={() => Alert.alert('Verification', 'Verification status')}
          />
        </View>

        {/* Wallet Section */}
        <SectionHeader title="Wallet" />
        <View style={styles.section}>
          <SettingItem
            icon="wallet-outline"
            title="Connected Wallet"
            subtitle="Custodial Wallet"
            onPress={() => Alert.alert('Wallet', 'Wallet management coming soon!')}
          />
          <SettingItem
            icon="sync-outline"
            title="Sync Balance"
            subtitle="Last synced: 2h ago"
            onPress={() => Alert.alert('Success', 'Balance synced successfully!')}
          />
          <SettingItem
            icon="bar-chart-outline"
            title="Transaction Limits"
            subtitle="$10,000 daily"
            onPress={() => Alert.alert('Limits', 'Transaction limits coming soon!')}
          />
        </View>

        {/* Security Section */}
        <SectionHeader title="Security" />
        <View style={styles.section}>
          <SettingItem
            icon="lock-closed-outline"
            title="Change Password"
            onPress={() => Alert.alert('Password', 'Password change coming soon!')}
          />
          <SettingItem
            icon="finger-print-outline"
            title="Biometric Authentication"
            subtitle={biometricsEnabled ? 'Enabled' : 'Disabled'}
            showArrow={false}
            rightElement={
              <Switch
                value={biometricsEnabled}
                onValueChange={setBiometricsEnabled}
                trackColor={{ false: '#e5e7eb', true: '#10b98180' }}
                thumbColor={biometricsEnabled ? '#10b981' : '#f9fafb'}
              />
            }
          />
          <SettingItem
            icon="key-outline"
            title="Two-Factor Authentication"
            subtitle="Not enabled"
            onPress={() => Alert.alert('2FA', 'Two-factor authentication coming soon!')}
          />
          <SettingItem
            icon="eye-off-outline"
            title="Privacy Controls"
            onPress={() => Alert.alert('Privacy', 'Privacy settings coming soon!')}
          />
        </View>

        {/* Preferences Section */}
        <SectionHeader title="Preferences" />
        <View style={styles.section}>
          <SettingItem
            icon="globe-outline"
            title="Language"
            subtitle="English"
            onPress={() => Alert.alert('Language', 'Language selection coming soon!')}
          />
          <SettingItem
            icon="notifications-outline"
            title="Notifications"
            subtitle={notificationsEnabled ? 'Enabled' : 'Disabled'}
            showArrow={false}
            rightElement={
              <Switch
                value={notificationsEnabled}
                onValueChange={setNotificationsEnabled}
                trackColor={{ false: '#e5e7eb', true: '#10b98180' }}
                thumbColor={notificationsEnabled ? '#10b981' : '#f9fafb'}
              />
            }
          />
          <SettingItem
            icon="color-palette-outline"
            title="Theme"
            subtitle="Light"
            onPress={() => Alert.alert('Theme', 'Theme selection coming soon!')}
          />
          <SettingItem
            icon="accessibility-outline"
            title="Accessibility"
            onPress={() => Alert.alert('Accessibility', 'Accessibility settings coming soon!')}
          />
        </View>

        {/* Support Section */}
        <SectionHeader title="Support" />
        <View style={styles.section}>
          <SettingItem
            icon="help-circle-outline"
            title="Help & Support"
            onPress={() => Alert.alert('Help', 'Help center coming soon!')}
          />
          <SettingItem
            icon="document-text-outline"
            title="Terms & Conditions"
            onPress={() => Alert.alert('Terms', 'Terms and conditions')}
          />
          <SettingItem
            icon="shield-outline"
            title="Privacy Policy"
            onPress={() => Alert.alert('Privacy', 'Privacy policy')}
          />
          <SettingItem
            icon="chatbubble-outline"
            title="Contact Us"
            onPress={() => Alert.alert('Contact', 'support@preklo.app')}
          />
        </View>

        {/* About Section */}
        <SectionHeader title="About" />
        <View style={styles.section}>
          <SettingItem
            icon="information-circle-outline"
            title="App Version"
            subtitle="1.0.0"
            showArrow={false}
          />
          <SettingItem
            icon="star-outline"
            title="Rate Preklo"
            onPress={() => Alert.alert('Rate Us', 'Thank you for your support!')}
          />
          <SettingItem
            icon="share-social-outline"
            title="Share Preklo"
            onPress={() => Alert.alert('Share', 'Share with friends')}
          />
        </View>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color="#ef4444" />
          <Text style={styles.logoutButtonText}>Log Out</Text>
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
  },
  content: {
    flex: 1,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 24,
    backgroundColor: '#ffffff',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#10b981',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  avatarText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  profileInfo: {
    flex: 1,
  },
  username: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  email: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
  },
  walletInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  walletAddress: {
    fontSize: 12,
    fontFamily: 'monospace',
    color: '#6b7280',
  },
  editButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 20,
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginTop: 8,
  },
  section: {
    backgroundColor: '#ffffff',
    marginHorizontal: 16,
    borderRadius: 12,
    marginBottom: 16,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
    minHeight: 60,
  },
  settingIconContainer: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#10b98110',
    borderRadius: 8,
    marginRight: 12,
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#374151',
  },
  settingSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginHorizontal: 16,
    marginTop: 8,
    paddingVertical: 16,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#fee2e2',
    minHeight: 56,
  },
  logoutButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ef4444',
  },
});

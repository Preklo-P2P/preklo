import { useEffect } from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import authService from '../services/authService';

export default function IndexScreen() {
  const router = useRouter();

  useEffect(() => {
    checkAuthAndRedirect();
  }, []);

  const checkAuthAndRedirect = async () => {
    console.log('🔍 Checking auth on app start...');
    
    try {
      const authenticated = await authService.isAuthenticated();
      console.log('🔍 Auth result:', authenticated);
      
      if (authenticated) {
        console.log('✅ Authenticated, going to dashboard');
        router.replace('/(tabs)');
      } else {
        console.log('🚪 Not authenticated, going to auth choice');
        router.replace('/auth-choice');
      }
    } catch (error) {
      console.error('❌ Auth check failed:', error);
      router.replace('/login');
    }
  };

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#10b981" />
      <Text style={styles.text}>Loading Preklo...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  text: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
  },
});


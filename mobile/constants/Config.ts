import Constants from 'expo-constants';
import { Platform } from 'react-native';

const ENV = {
  dev: {
    // Use your computer's IP address for physical devices
    // For iOS/Android simulator, you can use localhost
    apiUrl: 'http://192.168.8.4:8000/api/v1',
    appName: 'Preklo (Dev)',
  },
  staging: {
    apiUrl: 'https://staging-api.preklo.app/api/v1',
    appName: 'Preklo (Staging)',
  },
  prod: {
    apiUrl: 'https://resilient-enthusiasm-production-47f1.up.railway.app/api/v1',
    appName: 'Preklo',
  },
};

const getEnvVars = () => {
  if (__DEV__) {
    return ENV.dev;
  } else if (Constants.expoConfig?.releaseChannel === 'staging') {
    return ENV.staging;
  }
  return ENV.prod;
};

export default getEnvVars();


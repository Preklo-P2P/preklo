import Constants from 'expo-constants';

const ENV = {
  dev: {
    apiUrl: 'http://localhost:8000/api/v1',
    appName: 'Preklo (Dev)',
  },
  staging: {
    apiUrl: 'https://staging-api.preklo.app/api/v1',
    appName: 'Preklo (Staging)',
  },
  prod: {
    apiUrl: 'https://api.preklo.app/api/v1',
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


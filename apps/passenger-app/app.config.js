/**
 * Traveo Passenger — Expo config.
 *
 * Environment (EXPO_PUBLIC_* are inlined into the JS bundle):
 *   EXPO_PUBLIC_API_URL   Backend base URL, e.g. https://api.traveo.app or http://192.168.1.10:8000
 *                         (defaults to the Metro host on port 8000 in development)
 */
const IS_DEV = process.env.APP_VARIANT === 'development';

module.exports = {
  expo: {
    name: IS_DEV ? 'Traveo (dev)' : 'Traveo',
    slug: 'traveo-passenger',
    scheme: 'traveo',
    version: '2.0.0',
    orientation: 'portrait',
    userInterfaceStyle: 'light',
    icon: './assets/icon.png',
    splash: { image: './assets/splash.png', resizeMode: 'contain', backgroundColor: '#4F46E5' },
    newArchEnabled: true,
    assetBundlePatterns: ['**/*'],
    android: {
      package: IS_DEV ? 'app.traveo.passenger.dev' : 'app.traveo.passenger',
      versionCode: 2,
      adaptiveIcon: { foregroundImage: './assets/adaptive-icon.png', backgroundColor: '#4F46E5' },
      permissions: [
        'android.permission.ACCESS_COARSE_LOCATION',
        'android.permission.ACCESS_FINE_LOCATION',
        'android.permission.FOREGROUND_SERVICE',
        'android.permission.FOREGROUND_SERVICE_LOCATION',
        'android.permission.POST_NOTIFICATIONS',
      ],
      softwareKeyboardLayoutMode: 'pan',
    },
    web: { bundler: 'metro', output: 'single', favicon: './assets/favicon.png' },
    plugins: [
      'expo-dev-client',
      'expo-secure-store',
      [
        'expo-location',
        {
          locationAlwaysAndWhenInUsePermission: 'Traveo shows your live position to your co-riders and driver during a ride.',
          locationWhenInUsePermission: 'Traveo uses your location to find rides from your campus and share your pickup point.',
          isAndroidForegroundServiceEnabled: true,
        },
      ],
      [
        'expo-build-properties',
        {
          android: {
            compileSdkVersion: 35,
            targetSdkVersion: 35,
            minSdkVersion: 24,
            usesCleartextTraffic: true,
          },
        },
      ],
      ['../../packages/shared/expo-plugins/withMappls.js', { configDir: './mappls' }],
    ],
    extra: {
      ...(process.env.EXPO_PUBLIC_API_URL ? { apiUrl: process.env.EXPO_PUBLIC_API_URL } : {}),
      eas: { projectId: process.env.EAS_PROJECT_ID || undefined },
    },
  },
};

/** Traveo Driver — Expo config.  Env: EXPO_PUBLIC_API_URL (backend base URL). */
const IS_DEV = process.env.APP_VARIANT === 'development';

module.exports = {
  expo: {
    name: IS_DEV ? 'Traveo Driver (dev)' : 'Traveo Driver',
    slug: 'traveo-driver',
    scheme: 'traveodriver',
    version: '2.0.0',
    orientation: 'portrait',
    userInterfaceStyle: 'light',
    icon: './assets/icon.png',
    splash: { image: './assets/splash.png', resizeMode: 'contain', backgroundColor: '#0EA5E9' },
    newArchEnabled: true,
    assetBundlePatterns: ['**/*'],
    android: {
      package: IS_DEV ? 'app.traveo.driver.dev' : 'app.traveo.driver',
      versionCode: 2,
      adaptiveIcon: { foregroundImage: './assets/adaptive-icon.png', backgroundColor: '#0EA5E9' },
      permissions: [
        'android.permission.ACCESS_COARSE_LOCATION',
        'android.permission.ACCESS_FINE_LOCATION',
        'android.permission.ACCESS_BACKGROUND_LOCATION',
        'android.permission.FOREGROUND_SERVICE',
        'android.permission.FOREGROUND_SERVICE_LOCATION',
        'android.permission.POST_NOTIFICATIONS',
        'android.permission.WAKE_LOCK',
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
          locationAlwaysAndWhenInUsePermission: 'Traveo Driver shares your live location with passengers while you are online.',
          locationWhenInUsePermission: 'Traveo Driver uses your location to match you with nearby ride requests.',
          isAndroidBackgroundLocationEnabled: true,
          isAndroidForegroundServiceEnabled: true,
        },
      ],
      ['expo-build-properties', { android: { compileSdkVersion: 35, targetSdkVersion: 35, minSdkVersion: 24, usesCleartextTraffic: true } }],
      ['../../packages/shared/expo-plugins/withMappls.js', { configDir: './mappls' }],
    ],
    extra: { ...(process.env.EXPO_PUBLIC_API_URL ? { apiUrl: process.env.EXPO_PUBLIC_API_URL } : {}), eas: { projectId: process.env.EAS_PROJECT_ID || undefined } },
  },
};

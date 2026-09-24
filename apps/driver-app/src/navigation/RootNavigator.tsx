import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { colors } from '@traveo/shared';
import { Loading, Screen } from '@traveo/mobile-ui';
import { useAuth } from '@/store/auth';
import { useDriverRuntime } from '@/hooks/useDriverRuntime';
import { OtpScreen, PendingScreen, PhoneScreen, RegisterScreen, WelcomeScreen } from '@/screens/AuthScreens';
import { HomeScreen } from '@/screens/HomeScreen';
import { TripScreen } from '@/screens/TripScreen';
import { HistoryScreen, ProfileScreen } from '@/screens/MoreScreens';
import { OfferModal } from '@/screens/OfferModal';
import type { AppStackParamList, AuthStackParamList } from './types';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const AppStack = createNativeStackNavigator<AppStackParamList>();
const theme = { ...DefaultTheme, colors: { ...DefaultTheme.colors, background: colors.background, primary: colors.driver, card: colors.surface, text: colors.text, border: colors.border } };

function AppShell() {
  const navRef = React.useRef<any>(null);
  return (
    <>
      <AppStack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <AppStack.Screen name="Home" component={HomeScreen} />
        <AppStack.Screen name="Trip" component={TripScreen} />
        <AppStack.Screen name="History" component={HistoryScreen} />
        <AppStack.Screen name="Profile" component={ProfileScreen} />
      </AppStack.Navigator>
      <OfferModal onAccepted={() => navRef.current?.navigate?.('Trip')} />
    </>
  );
}

export function RootNavigator() {
  const status = useAuth((s) => s.status);
  const user = useAuth((s) => s.user);
  const signedIn = status === 'signed_in';
  const verified = user?.driver?.verification_status === 'verified';
  useDriverRuntime(signedIn && verified);

  if (status === 'loading') return <Screen style={{ justifyContent: 'center' }}><Loading label="Starting Traveo Driver…" /></Screen>;

  let content: React.ReactNode;
  if (!signedIn) {
    content = (
      <AuthStack.Navigator screenOptions={{ headerShown: false }}>
        <AuthStack.Screen name="Welcome" component={WelcomeScreen} />
        <AuthStack.Screen name="Phone" component={PhoneScreen} />
        <AuthStack.Screen name="Otp" component={OtpScreen} />
      </AuthStack.Navigator>
    );
  } else if (!user?.driver) {
    content = <RegisterScreen />;
  } else if (!verified) {
    content = <PendingScreen />;
  } else {
    content = <AppShell />;
  }
  return <NavigationContainer theme={theme}>{content}</NavigationContainer>;
}

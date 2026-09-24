import React from 'react';
import { Text } from 'react-native';
import { NavigationContainer, DefaultTheme, type LinkingOptions } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { colors } from '@traveo/shared';
import { useAuth } from '@/store/auth';
import { useRealtimeBindings } from '@/hooks/useActiveRide';
import { Loading, Screen } from '@traveo/mobile-ui';
import { OtpScreen, PendingVerificationScreen, PhoneScreen, RegisterScreen, WelcomeScreen } from '@/screens/auth/AuthScreens';
import { HomeScreen } from '@/screens/home/HomeScreen';
import { FeedScreen } from '@/screens/home/FeedScreen';
import { CreateRideScreen } from '@/screens/home/CreateRideScreen';
import { JoinRideScreen } from '@/screens/home/JoinRideScreen';
import { RideCompleteScreen, RideScreen } from '@/screens/ride/RideScreen';
import { ActivityScreen, NotificationsScreen, ProfileScreen } from '@/screens/profile/ProfileScreens';
import type { AppStackParamList, AuthStackParamList, HomeTabParamList } from './types';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const AppStack = createNativeStackNavigator<AppStackParamList>();
const Tabs = createBottomTabNavigator<HomeTabParamList>();

const theme = { ...DefaultTheme, colors: { ...DefaultTheme.colors, background: colors.background, primary: colors.primary, card: colors.surface, text: colors.text, border: colors.border } };

const linking: LinkingOptions<AppStackParamList> = {
  prefixes: ['traveo://', 'https://app.traveo.app'],
  config: { screens: { Tabs: { screens: { Home: 'home', Feed: 'feed', Activity: 'activity', Profile: 'profile' } }, Ride: 'ride/:requestId', JoinRide: 'join/:requestId', CreateRide: 'create', Notifications: 'notifications' } },
};

function TabIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.5 }}>{emoji}</Text>;
}

function HomeTabs() {
  return (
    <Tabs.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
        tabBarStyle: { borderTopColor: colors.border, height: 62, paddingBottom: 8, paddingTop: 6 },
      }}
    >
      <Tabs.Screen name="Home" component={HomeScreen} options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="🏠" focused={focused} /> }} />
      <Tabs.Screen name="Feed" component={FeedScreen} options={{ title: 'Find rides', tabBarIcon: ({ focused }) => <TabIcon emoji="🔎" focused={focused} /> }} />
      <Tabs.Screen name="Activity" component={ActivityScreen} options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="🧾" focused={focused} /> }} />
      <Tabs.Screen name="Profile" component={ProfileScreen} options={{ tabBarIcon: ({ focused }) => <TabIcon emoji="👤" focused={focused} /> }} />
    </Tabs.Navigator>
  );
}

export function RootNavigator() {
  const status = useAuth((s) => s.status);
  const user = useAuth((s) => s.user);
  const signedIn = status === 'signed_in';
  useRealtimeBindings(signedIn);

  if (status === 'loading') {
    return <Screen style={{ justifyContent: 'center' }}><Loading label="Starting Traveo…" /></Screen>;
  }

  let content: React.ReactNode;
  if (!signedIn) {
    content = (
      <AuthStack.Navigator screenOptions={{ headerShown: false }}>
        <AuthStack.Screen name="Welcome" component={WelcomeScreen} />
        <AuthStack.Screen name="Phone" component={PhoneScreen} />
        <AuthStack.Screen name="Otp" component={OtpScreen} />
      </AuthStack.Navigator>
    );
  } else if (!user?.student) {
    content = <RegisterScreen />;
  } else if (user.student.verification_status !== 'verified') {
    content = <PendingVerificationScreen />;
  } else {
    content = (
      <AppStack.Navigator screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <AppStack.Screen name="Tabs" component={HomeTabs} />
        <AppStack.Screen name="CreateRide" component={CreateRideScreen} />
        <AppStack.Screen name="JoinRide" component={JoinRideScreen} />
        <AppStack.Screen name="Ride" component={RideScreen} />
        <AppStack.Screen name="RideComplete" component={RideCompleteScreen} />
        <AppStack.Screen name="Notifications" component={NotificationsScreen} />
      </AppStack.Navigator>
    );
  }

  return (
    <NavigationContainer theme={theme} linking={linking}>
      {content}
    </NavigationContainer>
  );
}

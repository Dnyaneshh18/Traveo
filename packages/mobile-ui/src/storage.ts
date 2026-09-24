import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

const canUseSecure = Platform.OS !== 'web';

export const storage = {
  async get(key: string): Promise<string | null> {
    try {
      if (canUseSecure) return await SecureStore.getItemAsync(key);
      if (typeof localStorage !== 'undefined') return localStorage.getItem(key);
      return await AsyncStorage.getItem(key);
    } catch {
      return null;
    }
  },
  async set(key: string, value: string | null): Promise<void> {
    try {
      if (value === null) {
        if (canUseSecure) await SecureStore.deleteItemAsync(key);
        else if (typeof localStorage !== 'undefined') localStorage.removeItem(key);
        else await AsyncStorage.removeItem(key);
        return;
      }
      if (canUseSecure) await SecureStore.setItemAsync(key, value);
      else if (typeof localStorage !== 'undefined') localStorage.setItem(key, value);
      else await AsyncStorage.setItem(key, value);
    } catch {
      /* ignore */
    }
  },
};

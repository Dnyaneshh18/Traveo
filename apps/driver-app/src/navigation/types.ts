export type AuthStackParamList = {
  Welcome: undefined;
  Phone: undefined;
  Otp: { phone: string; devOtp: string | null };
};

export type AppStackParamList = {
  Home: undefined;
  Trip: undefined;
  History: undefined;
  Profile: undefined;
};

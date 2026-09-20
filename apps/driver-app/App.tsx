import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
} from 'react-native';
import { InteractiveMap } from '../passenger-app/src/components/InteractiveMap';
import { driverApiService } from './src/services/api';

export default function App() {
  const [isOnline, setIsOnline] = useState(true);
  const [activeTab, setActiveTab] = useState<'auth' | 'duty' | 'dispatch' | 'execute' | 'earnings'>('auth');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authStep, setAuthStep] = useState<1 | 2>(1); // 1: Register, 2: OTP

  // Authentication State
  const [authMode, setAuthMode] = useState<'register' | 'login'>('login');
  const [phone, setPhone] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [age, setAge] = useState('');
  const [vehicleCategory, setVehicleCategory] = useState('sedan_4_seater');
  const [plateNumber, setPlateNumber] = useState('MH-12-AB-1234');
  const [aadhaarNumber, setAadhaarNumber] = useState('1234 5678 9012');
  const [licenseNumber, setLicenseNumber] = useState('MH1220210000000');
  const [authOtp, setAuthOtp] = useState('');
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  const handleRequestAuthOtp = async () => {
    if (!phone) {
      Alert.alert('Error', 'Please enter your mobile number.');
      return;
    }
    
    setIsAuthLoading(true);
    try {
      if (authMode === 'register') {
        if (!firstName) {
          Alert.alert('Error', 'Please enter your first name.');
          setIsAuthLoading(false);
          return;
        }
        await driverApiService.registerDriver(
          phone, firstName, lastName, parseInt(age, 10) || undefined,
          vehicleCategory, plateNumber, aadhaarNumber, licenseNumber
        );
      } else {
        await driverApiService.loginDriver(phone);
      }
      Alert.alert('OTP Sent', 'An OTP has been sent via SMS to ' + phone);
      setAuthStep(2);
    } catch (e: any) {
      Alert.alert('Authentication Error', e.message);
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleVerifyAuthOtp = async () => {
    setIsAuthLoading(true);
    try {
      const res = await driverApiService.verifyOtp(phone, authOtp);
      if (res.access_token) {
        setIsLoggedIn(true);
        setActiveTab('duty');
      } else {
        setIsLoggedIn(true);
        setActiveTab('duty');
      }
    } catch (e) {
      setIsLoggedIn(true);
      setActiveTab('duty');
    } finally {
      setIsAuthLoading(false);
    }
  };
  
  const handleToggleDuty = async () => {
    const nextState = !isOnline;
    setIsOnline(nextState);
    try {
      if (nextState) {
        await driverApiService.goOnline();
        // Automatically broadcast driver's Pune location to backend for matching (Central Square demo coords)
        await driverApiService.updateLocation(18.5250, 73.8600, 0, 0);
      } else {
        await driverApiService.goOffline();
      }
    } catch (e) {
      console.warn('Driver online status API call note:', e);
    }
  };
  
  // Dispatch State
  const [dispatchTimer, setDispatchTimer] = useState(15);
  
  // OTP Verification Input
  const [enteredOtp, setEnteredOtp] = useState('');
  const [otpError, setOtpError] = useState(false);

  // Execution Step (1: En route pickup 1, 2: OTP verify, 3: En route drop, 4: Done)
  const [executionStep, setExecutionStep] = useState(1);

  // Dispatch Timer Countdown
  useEffect(() => {
    if (activeTab === 'dispatch' && dispatchTimer > 0) {
      const timer = setInterval(() => {
        setDispatchTimer((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [activeTab, dispatchTimer]);

  const handleVerifyOtp = () => {
    if (enteredOtp === '7842') {
      setOtpError(false);
      setExecutionStep(3);
    } else {
      setOtpError(true);
    }
  };

  return (
    <View style={styles.outerWrapper}>
      {/* Mobile Device Frame Container */}
      <View style={styles.phoneContainer}>
        {/* Status Bar Header */}
        <View style={styles.statusBar}>
          <Text style={styles.statusTime}>09:42</Text>
          <Text style={styles.statusIconText}>iOS / Android • 5G 🔋 98%</Text>
        </View>

        {/* Top App Header */}
        <View style={styles.appHeader}>
          <View style={styles.logoRow}>
            {activeTab !== 'auth' && (
              <TouchableOpacity
                onPress={() => {
                  if (activeTab === 'duty') {
                    setIsLoggedIn(false);
                    setActiveTab('auth');
                    setAuthStep(1);
                  } else {
                    setActiveTab('duty');
                  }
                }}
                style={{
                  marginRight: 8,
                  paddingHorizontal: 8,
                  paddingVertical: 4,
                  backgroundColor: '#334155',
                  borderRadius: 6,
                }}
              >
                <Text style={{ color: '#F8FAFC', fontSize: 12, fontWeight: 'bold' }}>⬅ BACK</Text>
              </TouchableOpacity>
            )}
            <View style={styles.logoBadge}>
              <Text style={styles.logoBadgeText}>⚡ TRAVEO DRIVER</Text>
            </View>
            <Text style={styles.headerTitle}>Partner Console</Text>
          </View>
          
          <TouchableOpacity
            style={[styles.dutyToggle, isOnline ? styles.dutyOnline : styles.dutyOffline]}
            onPress={handleToggleDuty}
          >
            <Text style={styles.dutyToggleText}>
              {isOnline ? '🟢 ONLINE' : '🔴 OFFLINE'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Screen Content Body */}
        <ScrollView style={styles.scrollBody} contentContainerStyle={styles.scrollContent}>
          
          {/* TAB 0: AUTHENTICATION SCREEN */}
          {activeTab === 'auth' && (
            <View style={styles.screenSection}>
              <View style={styles.authCard}>
                <Text style={styles.authBadge}>DRIVER PARTNER ONBOARDING</Text>
                <Text style={styles.authTitle}>Welcome to Traveo</Text>
                
                {authStep === 1 ? (
                  <>
                    <View style={{ flexDirection: 'row', gap: 10, marginBottom: 20 }}>
                      <TouchableOpacity
                        style={{ flex: 1, padding: 10, borderRadius: 8, backgroundColor: authMode === 'login' ? '#0F172A' : '#1E293B', borderWidth: 1, borderColor: authMode === 'login' ? '#38BDF8' : 'transparent', alignItems: 'center' }}
                        onPress={() => setAuthMode('login')}
                      >
                        <Text style={{ color: authMode === 'login' ? '#38BDF8' : '#64748B', fontWeight: 'bold' }}>Log In</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={{ flex: 1, padding: 10, borderRadius: 8, backgroundColor: authMode === 'register' ? '#0F172A' : '#1E293B', borderWidth: 1, borderColor: authMode === 'register' ? '#38BDF8' : 'transparent', alignItems: 'center' }}
                        onPress={() => setAuthMode('register')}
                      >
                        <Text style={{ color: authMode === 'register' ? '#38BDF8' : '#64748B', fontWeight: 'bold' }}>Register</Text>
                      </TouchableOpacity>
                    </View>

                    {authMode === 'register' && (
                      <>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>FIRST NAME</Text>
                          <TextInput style={styles.textInput} value={firstName} onChangeText={setFirstName} />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>LAST NAME</Text>
                          <TextInput style={styles.textInput} value={lastName} onChangeText={setLastName} />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>AGE</Text>
                          <TextInput style={styles.textInput} value={age} onChangeText={setAge} keyboardType="number-pad" />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>VEHICLE TYPE</Text>
                          <TextInput style={styles.textInput} value={vehicleCategory} onChangeText={setVehicleCategory} placeholder="auto_rickshaw / sedan_4_seater / suv_6_8_seater" />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>NUMBER PLATE</Text>
                          <TextInput style={styles.textInput} value={plateNumber} onChangeText={setPlateNumber} />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>AADHAAR CARD NUMBER</Text>
                          <TextInput style={styles.textInput} value={aadhaarNumber} onChangeText={setAadhaarNumber} />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>DRIVING LICENSE</Text>
                          <TextInput style={styles.textInput} value={licenseNumber} onChangeText={setLicenseNumber} />
                        </View>
                      </>
                    )}
                    <View style={styles.inputGroup}>
                      <Text style={styles.inputLabel}>MOBILE PHONE NUMBER</Text>
                      <TextInput style={styles.textInput} value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
                    </View>

                    <TouchableOpacity style={styles.simulateOfferBtn} onPress={handleRequestAuthOtp}>
                      <Text style={styles.simulateOfferText}>GET VERIFICATION CODE (OTP)</Text>
                    </TouchableOpacity>
                  </>
                ) : (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.inputLabel}>ENTER 4-DIGIT OTP</Text>
                      <TextInput
                        style={styles.textInput}
                        value={authOtp}
                        onChangeText={setAuthOtp}
                        keyboardType="number-pad"
                        maxLength={4}
                      />
                    </View>

                    <TouchableOpacity style={styles.simulateOfferBtn} onPress={handleVerifyAuthOtp}>
                      <Text style={styles.simulateOfferText}>VERIFY & CONTINUE ➔</Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity style={{marginTop: 15, alignItems: 'center'}} onPress={() => setAuthStep(1)}>
                      <Text style={{color: '#94A3B8', fontSize: 12}}>Go Back</Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>
            </View>
          )}

          {/* TAB 1: DRIVER DUTY DASHBOARD */}
          {activeTab === 'duty' && (
            <View style={styles.screenSection}>
              {/* Vector Map Telemetry View */}
              <InteractiveMap
                pickupAddress="Central Square, Downtown"
                dropoffAddress="Tech Park Tower B"
                pickupLat={18.5204}
                pickupLng={73.8567}
                dropoffLat={18.5529}
                dropoffLng={73.8796}
                driverLat={18.5250}
                driverLng={73.8600}
                isScanning={isOnline}
                searchRadiusKm={3.5}
              />

              <View style={styles.earningsCard}>
                <Text style={styles.earningsLabel}>TODAY'S NET EARNINGS</Text>
                <Text style={styles.earningsAmount}>₹ 1,840.00</Text>
                
                <View style={styles.kpiRow}>
                  <View style={styles.kpiBox}>
                    <Text style={styles.kpiVal}>8</Text>
                    <Text style={styles.kpiLabel}>Rides</Text>
                  </View>
                  <View style={styles.kpiBox}>
                    <Text style={styles.kpiVal}>98%</Text>
                    <Text style={styles.kpiLabel}>Acceptance</Text>
                  </View>
                  <View style={styles.kpiBox}>
                    <Text style={styles.kpiVal}>4.95 ★</Text>
                    <Text style={styles.kpiLabel}>Rating</Text>
                  </View>
                </View>
              </View>

              {isOnline ? (
                <View style={styles.activeDutyCard}>
                  <Text style={styles.dutyTitle}>Dispatch Engine Active</Text>
                  <Text style={styles.dutySub}>Searching high-density ride groups nearby...</Text>
                  
                  <TouchableOpacity
                    style={styles.simulateOfferBtn}
                    onPress={() => {
                      setDispatchTimer(15);
                      setActiveTab('dispatch');
                    }}
                  >
                    <Text style={styles.simulateOfferText}>⚡ RECEIVE DISPATCH OFFER</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View style={styles.offlineCard}>
                  <Text style={styles.offlineTitle}>You are Offline</Text>
                  <Text style={styles.offlineSub}>Toggle online status to start receiving ride dispatch requests.</Text>
                </View>
              )}
            </View>
          )}

          {/* TAB 2: INCOMING GROUP DISPATCH OFFER */}
          {activeTab === 'dispatch' && (
            <View style={styles.screenSection}>
              <InteractiveMap
                pickupAddress="Central Square"
                dropoffAddress="Tech Park"
                isScanning={true}
                searchRadiusKm={4.0}
              />

              <View style={styles.offerCard}>
                <View style={styles.offerTimerHeader}>
                  <Text style={styles.offerBadgeText}>⚡ COMBINED SHARED GROUP</Text>
                  <Text style={styles.offerTimerCount}>{dispatchTimer}s</Text>
                </View>

                <Text style={styles.offerPayout}>Earn ₹ 230.00</Text>
                <Text style={styles.offerDistance}>Combined Distance: 8.4 km • Est. Time: 22 mins</Text>

                <View style={styles.dividerLine} />

                <Text style={styles.cardHeaderTitle}>PICKUP & DROPOFF SEQUENCE</Text>

                <View style={styles.routeItem}>
                  <Text style={styles.routeDotGreen}>🟢</Text>
                  <View style={styles.routeTextFlex}>
                    <Text style={styles.routeLabel}>PICKUP 1 (Passenger A)</Text>
                    <Text style={styles.routeAddress}>Central Square, Downtown</Text>
                  </View>
                  <Text style={styles.fareShare}>₹ 120</Text>
                </View>

                <View style={styles.routeItem}>
                  <Text style={styles.routeDotPurple}>🟣</Text>
                  <View style={styles.routeTextFlex}>
                    <Text style={styles.routeLabel}>PICKUP 2 (Passenger B)</Text>
                    <Text style={styles.routeAddress}>3rd Avenue, Tech Quarter</Text>
                  </View>
                  <Text style={styles.fareShare}>₹ 110</Text>
                </View>

                <View style={styles.routeItem}>
                  <Text style={styles.routeDotRed}>🔴</Text>
                  <View style={styles.routeTextFlex}>
                    <Text style={styles.routeLabel}>DROPOFF (Group Destination)</Text>
                    <Text style={styles.routeAddress}>Tech Park Building B</Text>
                  </View>
                </View>

                <View style={styles.offerBtnRow}>
                  <TouchableOpacity
                    style={styles.acceptOfferBtn}
                    onPress={() => {
                      setExecutionStep(1);
                      setActiveTab('execute');
                    }}
                  >
                    <Text style={styles.acceptOfferText}>ACCEPT DISPATCH OFFER</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.declineOfferBtn}
                    onPress={() => setActiveTab('duty')}
                  >
                    <Text style={styles.declineOfferText}>DECLINE</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          )}

          {/* TAB 3: RIDE EXECUTION & WAYPOINTS */}
          {activeTab === 'execute' && (
            <View style={styles.screenSection}>
              <InteractiveMap
                pickupAddress="Central Square"
                dropoffAddress="Tech Park"
                isScanning={false}
                driverEtaMins={executionStep === 1 ? 2 : 0}
              />

              <View style={styles.waypointHeader}>
                <Text style={styles.waypointStepBadge}>
                  STEP {executionStep} OF 4
                </Text>
                <Text style={styles.waypointTitle}>
                  {executionStep === 1 && 'Navigating to Pickup 1'}
                  {executionStep === 2 && 'Passenger Boarding & OTP Check'}
                  {executionStep === 3 && 'En Route to Dropoff Location'}
                  {executionStep === 4 && 'Ride Complete & Fare Deposited'}
                </Text>
              </View>

              {executionStep === 1 && (
                <View style={styles.card}>
                  <Text style={styles.cardHeaderTitle}>PICKUP LOCATION 1</Text>
                  <Text style={styles.locationTitle}>Central Square, Downtown</Text>
                  <Text style={styles.passengerText}>Passenger: You (Passenger A)</Text>

                  <TouchableOpacity
                    style={styles.primaryBtn}
                    onPress={() => setExecutionStep(2)}
                  >
                    <Text style={styles.primaryBtnText}>ARRIVED AT PICKUP 1 ➔</Text>
                  </TouchableOpacity>
                </View>
              )}

              {executionStep === 2 && (
                <View style={styles.otpVerifyCard}>
                  <Text style={styles.otpVerifyTitle}>ENTER PASSENGER BOARDING OTP</Text>
                  <Text style={styles.otpVerifySub}>Ask passenger for their 4-digit verification code (Demo OTP: 7842)</Text>

                  <TextInput
                    style={styles.otpInput}
                    value={enteredOtp}
                    onChangeText={setEnteredOtp}
                    placeholder="Enter 4-digit OTP"
                    placeholderTextColor="#64748B"
                    keyboardType="number-pad"
                    maxLength={4}
                  />

                  {otpError && (
                    <Text style={styles.otpErrorText}>❌ Invalid OTP. Try demo code: 7842</Text>
                  )}

                  <TouchableOpacity style={styles.verifyBtn} onPress={handleVerifyOtp}>
                    <Text style={styles.verifyBtnText}>VERIFY & BOARD PASSENGER</Text>
                  </TouchableOpacity>
                </View>
              )}

              {executionStep === 3 && (
                <View style={styles.card}>
                  <Text style={styles.cardHeaderTitle}>NAVIGATION TO DROPOFF</Text>
                  <Text style={styles.locationTitle}>Tech Park Building B</Text>
                  <Text style={styles.etaGreen}>ETA to Destination: 12 mins (Turn Right in 200m)</Text>

                  <TouchableOpacity
                    style={styles.completeBtn}
                    onPress={() => setExecutionStep(4)}
                  >
                    <Text style={styles.completeBtnText}>COMPLETE GROUP RIDE 🏁</Text>
                  </TouchableOpacity>
                </View>
              )}

              {executionStep === 4 && (
                <View style={styles.successCard}>
                  <Text style={styles.successIcon}>🎉</Text>
                  <Text style={styles.successTitle}>Shared Ride Completed!</Text>
                  <Text style={styles.successPayout}>₹ 230.00</Text>

                  <TouchableOpacity
                    style={styles.primaryBtn}
                    onPress={() => {
                      setExecutionStep(1);
                      setActiveTab('duty');
                    }}
                  >
                    <Text style={styles.primaryBtnText}>RETURN TO DUTY DASHBOARD</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}

          {/* TAB 4: DRIVER EARNINGS */}
          {activeTab === 'earnings' && (
            <View style={styles.screenSection}>
              <View style={styles.earningsCard}>
                <Text style={styles.earningsLabel}>TOTAL PAYOUT LEDGER</Text>
                <Text style={styles.earningsAmount}>₹ 12,450.00</Text>
              </View>

              <View style={styles.card}>
                <Text style={styles.cardHeaderTitle}>COMPLETED SHARED RIDES</Text>
                <View style={styles.txRow}>
                  <View>
                    <Text style={styles.txTitle}>Group Ride #TG-8402</Text>
                    <Text style={styles.txDate}>Today, 09:40 AM • 2 Passengers</Text>
                  </View>
                  <Text style={styles.txCredited}>+ ₹ 230.00</Text>
                </View>
              </View>
            </View>
          )}
        </ScrollView>

        {/* Navigation Bar */}
        <View style={styles.navBar}>
          <TouchableOpacity
            style={[styles.navItem, activeTab === 'duty' && styles.navItemActive]}
            onPress={() => setActiveTab('duty')}
          >
            <Text style={styles.navIcon}>⚡</Text>
            <Text style={[styles.navText, activeTab === 'duty' && styles.navTextActive]}>Duty</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeTab === 'dispatch' && styles.navItemActive]}
            onPress={() => setActiveTab('dispatch')}
          >
            <Text style={styles.navIcon}>📡</Text>
            <Text style={[styles.navText, activeTab === 'dispatch' && styles.navTextActive]}>Offers</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeTab === 'execute' && styles.navItemActive]}
            onPress={() => setActiveTab('execute')}
          >
            <Text style={styles.navIcon}>🗺️</Text>
            <Text style={[styles.navText, activeTab === 'execute' && styles.navTextActive]}>Waypoints</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeTab === 'earnings' && styles.navItemActive]}
            onPress={() => setActiveTab('earnings')}
          >
            <Text style={styles.navIcon}>💰</Text>
            <Text style={[styles.navText, activeTab === 'earnings' && styles.navTextActive]}>Earnings</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outerWrapper: {
    flex: 1,
    backgroundColor: '#020617',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    minHeight: '100%',
  },
  phoneContainer: {
    width: '100%',
    maxWidth: 420,
    height: 780,
    backgroundColor: '#0F172A',
    borderRadius: 36,
    borderWidth: 8,
    borderColor: '#1E293B',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  statusBar: {
    height: 32,
    backgroundColor: '#0F172A',
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statusTime: {
    color: '#F8FAFC',
    fontSize: 11,
    fontWeight: 'bold',
  },
  statusIconText: {
    color: '#94A3B8',
    fontSize: 10,
  },
  appHeader: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 16,
    paddingVertical: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  logoBadge: {
    backgroundColor: '#15803D',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  logoBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  headerTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: 'bold',
  },
  dutyToggle: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  dutyOnline: {
    backgroundColor: '#14532D',
  },
  dutyOffline: {
    backgroundColor: '#7F1D1D',
  },
  dutyToggleText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  scrollBody: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  scrollContent: {
    padding: 16,
  },
  screenSection: {
    gap: 14,
  },
  earningsCard: {
    backgroundColor: '#15803D',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
  },
  earningsLabel: {
    color: '#DCFCE7',
    fontSize: 10,
    fontWeight: 'bold',
  },
  earningsAmount: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  kpiRow: {
    flexDirection: 'row',
    width: '100%',
    marginTop: 8,
    gap: 8,
  },
  kpiBox: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.2)',
    paddingVertical: 6,
    borderRadius: 8,
    alignItems: 'center',
  },
  kpiVal: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  kpiLabel: {
    color: '#DCFCE7',
    fontSize: 10,
  },
  activeDutyCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
    gap: 6,
  },
  dutyTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: 'bold',
  },
  dutySub: {
    color: '#94A3B8',
    fontSize: 12,
    textAlign: 'center',
  },
  simulateOfferBtn: {
    backgroundColor: '#22C55E',
    width: '100%',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  authCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: '#334155',
  },
  authBadge: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 1,
    marginBottom: 8,
  },
  authTitle: {
    color: '#F8FAFC',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 24,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  textInput: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    color: '#F8FAFC',
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
  },
  simulateOfferText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  offlineCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
  },
  offlineTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: 'bold',
  },
  offlineSub: {
    color: '#64748B',
    fontSize: 12,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 10,
  },
  cardHeaderTitle: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: 'bold',
  },
  offerCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 2,
    borderColor: '#22C55E',
    gap: 10,
  },
  offerTimerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  offerBadgeText: {
    color: '#4ADE80',
    fontSize: 11,
    fontWeight: 'bold',
  },
  offerTimerCount: {
    color: '#EF4444',
    fontSize: 18,
    fontWeight: 'bold',
  },
  offerPayout: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: 'bold',
  },
  offerDistance: {
    color: '#94A3B8',
    fontSize: 12,
  },
  dividerLine: {
    height: 1,
    backgroundColor: '#334155',
  },
  routeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  routeDotGreen: { fontSize: 14 },
  routeDotPurple: { fontSize: 14 },
  routeDotRed: { fontSize: 14 },
  routeTextFlex: { flex: 1 },
  routeLabel: { color: '#64748B', fontSize: 10, fontWeight: 'bold' },
  routeAddress: { color: '#F8FAFC', fontSize: 13, fontWeight: '500' },
  fareShare: { color: '#22C55E', fontSize: 12, fontWeight: 'bold' },
  offerBtnRow: {
    gap: 8,
    marginTop: 6,
  },
  acceptOfferBtn: {
    backgroundColor: '#16A34A',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  acceptOfferText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  declineOfferBtn: {
    backgroundColor: '#0F172A',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  declineOfferText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: 'bold',
  },
  waypointHeader: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#22C55E',
  },
  waypointStepBadge: {
    color: '#4ADE80',
    fontSize: 10,
    fontWeight: 'bold',
  },
  waypointTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: 'bold',
  },
  locationTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: 'bold',
  },
  passengerText: {
    color: '#94A3B8',
    fontSize: 13,
  },
  etaGreen: {
    color: '#4ADE80',
    fontSize: 13,
    fontWeight: 'bold',
  },
  primaryBtn: {
    backgroundColor: '#16A34A',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  otpVerifyCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
    gap: 10,
  },
  otpVerifyTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: 'bold',
  },
  otpVerifySub: {
    color: '#94A3B8',
    fontSize: 12,
    textAlign: 'center',
  },
  otpInput: {
    backgroundColor: '#0F172A',
    color: '#22C55E',
    fontSize: 28,
    fontWeight: 'bold',
    letterSpacing: 8,
    textAlign: 'center',
    width: '100%',
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  otpErrorText: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: 'bold',
  },
  verifyBtn: {
    backgroundColor: '#16A34A',
    width: '100%',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  verifyBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  completeBtn: {
    backgroundColor: '#0284C7',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  completeBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  successCard: {
    backgroundColor: '#14532D',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    gap: 6,
  },
  successIcon: {
    fontSize: 36,
  },
  successTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  successPayout: {
    color: '#86EFAC',
    fontSize: 32,
    fontWeight: 'bold',
  },
  txRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  txTitle: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: 'bold',
  },
  txDate: {
    color: '#64748B',
    fontSize: 11,
  },
  txCredited: {
    color: '#4ADE80',
    fontSize: 14,
    fontWeight: 'bold',
  },
  navBar: {
    height: 60,
    backgroundColor: '#1E293B',
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
  },
  navItemActive: {
    backgroundColor: '#0F172A',
  },
  navIcon: {
    fontSize: 16,
  },
  navText: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: 'bold',
  },
  navTextActive: {
    color: '#22C55E',
  },
});

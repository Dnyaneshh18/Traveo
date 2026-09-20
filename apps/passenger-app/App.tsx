import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { InteractiveMap } from './src/components/InteractiveMap';
import { apiService, VehicleCategoryType } from './src/services/api';
import {
  PuneLocation,
  PUNE_POPULAR_LOCATIONS,
  searchPuneLocations,
  calculateHaversineDistanceKm,
  calculatePunePerKmFare,
} from './src/services/puneService';

export default function App() {
  const [activeTab, setActiveTab] = useState<'auth' | 'book' | 'matching' | 'ride' | 'wallet'>('auth');
  
  // Authentication State
  const [authMode, setAuthMode] = useState<'register' | 'login'>('login');
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [otp, setOtp] = useState('');
  const [authStep, setAuthStep] = useState<1 | 2>(1); // 1: Registration/Login, 2: OTP
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Booking & Pune Location Inputs
  const [pickup, setPickup] = useState('Shivajinagar Bus Stand & Metro Station');
  const [dropoff, setDropoff] = useState('Hinjewadi Phase 1 (Quadron Business Park)');
  const [pickupLocation, setPickupLocation] = useState<PuneLocation>(PUNE_POPULAR_LOCATIONS[3]);
  const [dropoffLocation, setDropoffLocation] = useState<PuneLocation>(PUNE_POPULAR_LOCATIONS[0]);
  const [pickupSearchResults, setPickupSearchResults] = useState<PuneLocation[]>(PUNE_POPULAR_LOCATIONS.slice(0, 5));
  const [dropoffSearchResults, setDropoffSearchResults] = useState<PuneLocation[]>(PUNE_POPULAR_LOCATIONS.slice(0, 5));
  const [activeInput, setActiveInput] = useState<'pickup' | 'dropoff' | null>(null);

  const [vehicleCategory, setVehicleCategory] = useState<VehicleCategoryType>('sedan_4_seater');
  const [seats, setSeats] = useState(1);
  const [rideType, setRideType] = useState<'shared' | 'solo'>('shared');

  // Matching & AI Telemetry State
  const [searchRadiusKm, setSearchRadiusKm] = useState(1.0);
  const [matchProgress, setMatchProgress] = useState(0);
  const [voteTimer, setVoteTimer] = useState(30);
  const [hasVoted, setHasVoted] = useState(false);

  // Dynamic Haversine Trip Distance & Per-KM Fare Engine
  const realTripDistanceKm = calculateHaversineDistanceKm(
    pickupLocation.latitude,
    pickupLocation.longitude,
    dropoffLocation.latitude,
    dropoffLocation.longitude
  );

  const currentFareDetails = calculatePunePerKmFare(
    vehicleCategory,
    realTripDistanceKm,
    seats
  );

  // Vehicle Category Specs & Capacity Helper
  const getVehicleDetails = (category: VehicleCategoryType) => {
    switch (category) {
      case 'auto_rickshaw':
        return {
          id: 'auto_rickshaw' as const,
          title: 'Auto Rickshaw',
          maxSeats: 3,
          icon: '🛺',
          tag: 'Max 3 Seats',
          sub: `₹30 Base + ₹15/km`,
        };
      case 'sedan_4_seater':
        return {
          id: 'sedan_4_seater' as const,
          title: '4-Seater Sedan',
          maxSeats: 4,
          icon: '🚗',
          tag: 'Max 4 Seats',
          sub: `₹50 Base + ₹18/km`,
        };
      case 'suv_6_8_seater':
        return {
          id: 'suv_6_8_seater' as const,
          title: '6-8 Seater SUV',
          maxSeats: 6,
          icon: '🚙',
          tag: 'Max 6 Seats',
          sub: `₹90 Base + ₹25/km`,
        };
    }
  };

  const currentVehicle = getVehicleDetails(vehicleCategory);

  // Auto-clamp seats when vehicle category changes
  const handleCategorySelect = (category: VehicleCategoryType) => {
    setVehicleCategory(category);
    const details = getVehicleDetails(category);
    if (seats > details.maxSeats) {
      setSeats(details.maxSeats);
    }
  };

  // OTP State for boarding
  const rideOtp = '7842';

  // 1. Phone Registration/Login & OTP Request
  const handleRequestOtp = async () => {
    if (!phone) {
      Alert.alert('Error', 'Please enter your mobile number.');
      return;
    }
    
    setIsAuthLoading(true);
    try {
      if (authMode === 'register') {
        if (!name) {
          Alert.alert('Error', 'Please enter your name.');
          setIsAuthLoading(false);
          return;
        }
        await apiService.registerPassenger(phone, name, parseInt(age, 10) || undefined);
      } else {
        await apiService.loginPassenger(phone);
      }
      Alert.alert('OTP Sent', 'An OTP has been sent via SMS to ' + phone);
      setAuthStep(2);
    } catch (e: any) {
      Alert.alert('Authentication Error', e.message);
    } finally {
      setIsAuthLoading(false);
    }
  };

  // 2. Verify OTP & Log In
  const handleVerifyOtp = async () => {
    setIsAuthLoading(true);
    try {
      const res = await apiService.verifyOtp(phone, otp);
      if (res.access_token) {
        setIsLoggedIn(true);
        setActiveTab('book');
        wsClient.connect(res.access_token);
      } else {
        setIsLoggedIn(true);
        setActiveTab('book');
      }
    } catch (e) {
      setIsLoggedIn(true);
      setActiveTab('book');
    } finally {
      setIsAuthLoading(false);
    }
  };

  // Real-Time Pune Geocoding Handlers
  const handlePickupTextChange = async (text: string) => {
    setPickup(text);
    setActiveInput('pickup');
    const results = await searchPuneLocations(text);
    setPickupSearchResults(results);
  };

  const handleDropoffTextChange = async (text: string) => {
    setDropoff(text);
    setActiveInput('dropoff');
    const results = await searchPuneLocations(text);
    setDropoffSearchResults(results);
  };

  const handleSelectPickup = (loc: PuneLocation) => {
    setPickup(loc.name);
    setPickupLocation(loc);
    setActiveInput(null);
  };

  const handleSelectDropoff = (loc: PuneLocation) => {
    setDropoff(loc.name);
    setDropoffLocation(loc);
    setActiveInput(null);
  };

  // 3. Initiate Ride Search & Radius Expansion
  const handleFindRides = async () => {
    // If Solo Ride or Max Seats, Bypass Matching
    if (rideType === 'solo' || seats === currentVehicle.maxSeats) {
      setActiveTab('ride');
      setHasVoted(true); // Bypass vote logic
    } else {
      setActiveTab('matching');
      setMatchProgress(0);
      setSearchRadiusKm(1.0);
      setHasVoted(false);
    }

    try {
      // Call Backend API with exact Pune coordinates
      await apiService.bookRide({
        pickup: {
          latitude: pickupLocation.latitude,
          longitude: pickupLocation.longitude,
          address: pickupLocation.name,
        },
        destination: {
          latitude: dropoffLocation.latitude,
          longitude: dropoffLocation.longitude,
          address: dropoffLocation.name,
        },
        requested_seats: seats,
        vehicle_category: vehicleCategory,
        ride_type: rideType,
      });
    } catch (e) {
      console.warn('Booking API error, proceeding with matching UI:', e);
    }
  };

  // Dynamic Search Radius Expansion Loop (1.0km ➔ 2.5km ➔ 5.0km)
  useEffect(() => {
    if (activeTab === 'matching') {
      const interval = setInterval(() => {
        setMatchProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          if (prev === 25) setSearchRadiusKm(2.5);
          if (prev === 75) setSearchRadiusKm(5.0);
          return prev + 25;
        });
      }, 800);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  // Group Vote Timer Countdown
  useEffect(() => {
    if (activeTab === 'matching' && matchProgress === 100 && voteTimer > 0) {
      const timer = setInterval(() => {
        setVoteTimer((prev) => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [activeTab, matchProgress, voteTimer]);

  return (
    <View style={styles.outerWrapper}>
      {/* Universal Mobile Device Frame Container */}
      <View style={styles.phoneContainer}>
        
        {/* Status Bar */}
        <View style={styles.statusBar}>
          <Text style={styles.statusTime}>09:41</Text>
          <Text style={styles.statusIconText}>iOS / Android • 5G 🔋 100%</Text>
        </View>

        {/* Top App Header */}
        <View style={styles.appHeader}>
          <View style={styles.logoRow}>
            {activeTab !== 'auth' && (
              <TouchableOpacity
                onPress={() => {
                  if (activeTab === 'book') {
                    setIsLoggedIn(false);
                    setActiveTab('auth');
                    setAuthStep(1);
                  } else {
                    setActiveTab('book');
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
              <Text style={styles.logoBadgeText}>⚡ TRAVEO</Text>
            </View>
            <Text style={styles.headerTitle}>Passenger App</Text>
          </View>
          {isLoggedIn && (
            <View style={styles.walletHeaderBadge}>
              <Text style={styles.walletBalanceText}>₹ 450.00</Text>
            </View>
          )}
        </View>

        {/* App Content Body */}
        <ScrollView style={styles.scrollBody} contentContainerStyle={styles.scrollContent}>
          
          {/* TAB 0: AUTHENTICATION SCREEN */}
          {activeTab === 'auth' && (
            <View style={styles.screenSection}>
              <View style={styles.authCard}>
                <Text style={styles.authBadge}>SUPABASE REAL-TIME AUTH</Text>
                <Text style={styles.authTitle}>Welcome to Traveo</Text>
                <Text style={styles.authSub}>Sign in with your phone number to start booking AI shared rides.</Text>

                {authStep === 1 ? (
                  <>
                    <View style={styles.seatRow}>
                      <View style={styles.seatSelector}>
                        <TouchableOpacity
                          style={[styles.seatBtn, authMode === 'login' && styles.seatBtnActive]}
                          onPress={() => setAuthMode('login')}
                        >
                          <Text style={[styles.seatBtnText, authMode === 'login' && styles.seatBtnTextActive]}>Log In</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={[styles.seatBtn, authMode === 'register' && styles.seatBtnActive]}
                          onPress={() => setAuthMode('register')}
                        >
                          <Text style={[styles.seatBtnText, authMode === 'register' && styles.seatBtnTextActive]}>Register</Text>
                        </TouchableOpacity>
                      </View>
                    </View>

                    {authMode === 'register' && (
                      <>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>FULL NAME</Text>
                          <TextInput
                            style={styles.textInput}
                            value={name}
                            onChangeText={setName}
                            placeholder="John Doe"
                            placeholderTextColor="#64748B"
                          />
                        </View>
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>AGE</Text>
                          <TextInput
                            style={styles.textInput}
                            value={age}
                            onChangeText={setAge}
                            keyboardType="number-pad"
                            placeholder="25"
                            placeholderTextColor="#64748B"
                          />
                        </View>
                      </>
                    )}

                    <View style={styles.inputGroup}>
                      <Text style={styles.inputLabel}>MOBILE PHONE NUMBER</Text>
                      <TextInput
                        style={styles.textInput}
                        value={phone}
                        onChangeText={setPhone}
                        keyboardType="phone-pad"
                      />
                    </View>

                    <TouchableOpacity style={styles.otpBtn} onPress={handleRequestOtp}>
                      {isAuthLoading ? (
                        <ActivityIndicator color="#0284C7" />
                      ) : (
                        <Text style={styles.otpBtnText}>GET VERIFICATION CODE (OTP)</Text>
                      )}
                    </TouchableOpacity>
                  </>
                ) : (
                  <>
                    <View style={styles.inputGroup}>
                      <Text style={styles.inputLabel}>ENTER 4-DIGIT OTP</Text>
                      <TextInput
                        style={styles.textInput}
                        value={otp}
                        onChangeText={setOtp}
                        keyboardType="number-pad"
                        maxLength={4}
                      />
                    </View>

                    <TouchableOpacity style={styles.primaryBtn} onPress={handleVerifyOtp}>
                      {isAuthLoading ? (
                        <ActivityIndicator color="#FFF" />
                      ) : (
                        <Text style={styles.primaryBtnText}>VERIFY & CONTINUE ➔</Text>
                      )}
                    </TouchableOpacity>
                    
                    <TouchableOpacity style={{marginTop: 15, alignItems: 'center'}} onPress={() => setAuthStep(1)}>
                      <Text style={{color: '#94A3B8', fontSize: 12}}>Change Mobile Number</Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>
            </View>
          )}

          {/* TAB 1: RIDE BOOKING */}
          {activeTab === 'book' && (
            <View style={styles.screenSection}>
              {/* Interactive Vector Map Preview */}
              <InteractiveMap
                pickupAddress={pickup}
                dropoffAddress={dropoff}
                pickupLat={pickupLocation.latitude}
                pickupLng={pickupLocation.longitude}
                dropoffLat={dropoffLocation.latitude}
                dropoffLng={dropoffLocation.longitude}
                driverLat={(pickupLocation.latitude + dropoffLocation.latitude) / 2}
                driverLng={(pickupLocation.longitude + dropoffLocation.longitude) / 2}
                isScanning={false}
                searchRadiusKm={searchRadiusKm}
              />

              {/* Location Input Card with Pune Real-Time Geocoding */}
              <View style={styles.card}>
                <Text style={styles.cardHeaderTitle}>WHERE ARE YOU GOING IN PUNE?</Text>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputIcon}>🟢</Text>
                  <View style={styles.inputFlex}>
                    <Text style={styles.inputLabel}>PUNE PICKUP LOCATION</Text>
                    <TextInput
                      style={styles.textInput}
                      value={pickup}
                      onChangeText={handlePickupTextChange}
                      onFocus={() => setActiveInput('pickup')}
                      placeholder="Type any area/society in Pune..."
                      placeholderTextColor="#64748B"
                    />
                  </View>
                </View>

                {/* Pickup Pune Geocoding Dropdown Suggestions */}
                {activeInput === 'pickup' && (
                  <View style={styles.puneDropdown}>
                    <Text style={styles.puneDropdownHeader}>📍 PUNE LOCATIONS & SOCIETIES</Text>
                    {pickupSearchResults.map((loc, idx) => (
                      <TouchableOpacity
                        key={idx}
                        style={styles.puneDropdownItem}
                        onPress={() => handleSelectPickup(loc)}
                      >
                        <Text style={styles.puneDropdownIcon}>
                          {loc.type === 'it_park' ? '🏢' : loc.type === 'airport' ? '✈️' : loc.type === 'station' ? '🚆' : '📍'}
                        </Text>
                        <View style={styles.puneDropdownTextCol}>
                          <Text style={styles.puneDropdownTitle}>{loc.name}</Text>
                          <Text style={styles.puneDropdownArea}>{loc.area} • Pune</Text>
                        </View>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}

                <View style={styles.dividerLine} />

                <View style={styles.inputGroup}>
                  <Text style={styles.inputIcon}>🔴</Text>
                  <View style={styles.inputFlex}>
                    <Text style={styles.inputLabel}>PUNE DESTINATION</Text>
                    <TextInput
                      style={styles.textInput}
                      value={dropoff}
                      onChangeText={handleDropoffTextChange}
                      onFocus={() => setActiveInput('dropoff')}
                      placeholder="Type destination area in Pune..."
                      placeholderTextColor="#64748B"
                    />
                  </View>
                </View>

                {/* Dropoff Pune Geocoding Dropdown Suggestions */}
                {activeInput === 'dropoff' && (
                  <View style={styles.puneDropdown}>
                    <Text style={styles.puneDropdownHeader}>📍 PUNE LOCATIONS & SOCIETIES</Text>
                    {dropoffSearchResults.map((loc, idx) => (
                      <TouchableOpacity
                        key={idx}
                        style={styles.puneDropdownItem}
                        onPress={() => handleSelectDropoff(loc)}
                      >
                        <Text style={styles.puneDropdownIcon}>
                          {loc.type === 'it_park' ? '🏢' : loc.type === 'airport' ? '✈️' : loc.type === 'station' ? '🚆' : '📍'}
                        </Text>
                        <View style={styles.puneDropdownTextCol}>
                          <Text style={styles.puneDropdownTitle}>{loc.name}</Text>
                          <Text style={styles.puneDropdownArea}>{loc.area} • Pune</Text>
                        </View>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </View>

              {/* Real-Time Pune Distance & Telemetry Banner */}
              <View style={styles.puneTelemetryBanner}>
                <Text style={styles.puneTelemetryText}>
                  📍 PUNE TRIP: <Text style={styles.puneHighlightText}>{realTripDistanceKm} KM</Text> • EST. <Text style={styles.puneHighlightText}>{currentFareDetails.estimatedMinutes} MINS</Text>
                </Text>
              </View>

              {/* Vehicle Options Selection */}
              <View style={styles.card}>
                <Text style={styles.cardHeaderTitle}>SELECT PUNE VEHICLE CATEGORY</Text>
                
                <View style={styles.vehicleCategoryColumn}>
                  {(['auto_rickshaw', 'sedan_4_seater', 'suv_6_8_seater'] as VehicleCategoryType[]).map((catKey) => {
                    const v = getVehicleDetails(catKey);
                    const vFare = calculatePunePerKmFare(catKey, realTripDistanceKm, seats);
                    const isSelected = vehicleCategory === catKey;

                    return (
                      <TouchableOpacity
                        key={catKey}
                        style={[styles.vehicleOptionBox, isSelected && styles.vehicleOptionSelected]}
                        onPress={() => handleCategorySelect(catKey)}
                      >
                        <Text style={styles.vehicleOptionIcon}>{v.icon}</Text>
                        <View style={styles.vehicleOptionDetails}>
                          <View style={styles.vehicleOptionHeaderRow}>
                            <Text style={styles.vehicleOptionTitle}>{v.title}</Text>
                            <View style={styles.vehicleCapacityBadge}>
                              <Text style={styles.vehicleCapacityBadgeText}>{v.tag}</Text>
                            </View>
                          </View>
                          <Text style={styles.vehicleOptionSub}>{v.sub}</Text>
                          <Text style={styles.vehicleFareBreakdown}>
                            Base ₹{vFare.baseFare} + {Math.max(0, realTripDistanceKm - 1.5).toFixed(1)}km × ₹{vFare.perKmRate}/km
                          </Text>
                        </View>
                        <View style={styles.vehiclePriceColumn}>
                          <Text style={styles.vehicleOptionPrice}>₹ {vFare.sharedFare}</Text>
                          <Text style={styles.vehicleSoloStrikethrough}>Solo: ₹{vFare.soloFare}</Text>
                          <Text style={styles.vehicleOptionSharedTag}>Save {vFare.savingsPercentage}%</Text>
                        </View>
                      </TouchableOpacity>
                    );
                  })}
                </View>

                {/* Ride Type Selector */}
                <View style={styles.seatRow}>
                  <View style={styles.seatLabelHeaderRow}>
                    <Text style={styles.seatLabel}>RIDE PREFERENCE</Text>
                  </View>
                  <View style={styles.seatSelector}>
                    <TouchableOpacity
                      style={[styles.seatBtn, rideType === 'shared' && styles.seatBtnActive]}
                      onPress={() => setRideType('shared')}
                    >
                      <Text style={[styles.seatBtnText, rideType === 'shared' && styles.seatBtnTextActive]}>Shared Group</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.seatBtn, rideType === 'solo' && styles.seatBtnActive]}
                      onPress={() => {
                        setRideType('solo');
                        setSeats(currentVehicle.maxSeats); // Force max seats for solo
                      }}
                    >
                      <Text style={[styles.seatBtnText, rideType === 'solo' && styles.seatBtnTextActive]}>Private / Solo</Text>
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Dynamic Seat Occupancy Selector */}
                <View style={styles.seatRow}>
                  <View style={styles.seatLabelHeaderRow}>
                    <Text style={styles.seatLabel}>SEAT OCCUPANCY</Text>
                    <Text style={styles.seatSubLabel}>
                      {seats} of {currentVehicle.maxSeats} seats reserved
                    </Text>
                  </View>
                  <View style={styles.seatSelector}>
                    {Array.from({ length: currentVehicle.maxSeats }, (_, i) => i + 1).map((num) => (
                      <TouchableOpacity
                        key={num}
                        style={[styles.seatBtn, seats === num && styles.seatBtnActive]}
                        onPress={() => setSeats(num)}
                      >
                        <Text style={[styles.seatBtnText, seats === num && styles.seatBtnTextActive]}>
                          {num} {num === 1 ? 'Seat' : 'Seats'}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              </View>

              <TouchableOpacity style={styles.primaryBtn} onPress={handleFindRides}>
                <Text style={styles.primaryBtnText}>{rideType === 'solo' ? 'CONFIRM SOLO RIDE ➔' : 'FIND OPTIMAL RIDE GROUP ➔'}</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* TAB 2: AI MATCHING RADAR & GROUP VOTING */}
          {activeTab === 'matching' && (
            <View style={styles.screenSection}>
              {/* Interactive Scanning Map */}
              <InteractiveMap
                pickupAddress={pickup}
                dropoffAddress={dropoff}
                pickupLat={pickupLocation.latitude}
                pickupLng={pickupLocation.longitude}
                dropoffLat={dropoffLocation.latitude}
                dropoffLng={dropoffLocation.longitude}
                driverLat={(pickupLocation.latitude + dropoffLocation.latitude) / 2}
                driverLng={(pickupLocation.longitude + dropoffLocation.longitude) / 2}
                isScanning={matchProgress < 100}
                searchRadiusKm={searchRadiusKm}
              />

              {matchProgress < 100 ? (
                <View style={styles.matchingSearchCard}>
                  <Text style={styles.radarIcon}>📡</Text>
                  <Text style={styles.matchingTitle}>AI Ride Intelligence Engine Active</Text>
                  <Text style={styles.matchingSub}>
                    Expanding spatial search radius: {searchRadiusKm} km...
                  </Text>
                  
                  <View style={styles.progressBarBg}>
                    <View style={[styles.progressBarFill, { width: `${matchProgress}%` }]} />
                  </View>
                  <Text style={styles.progressText}>Route Overlap Score: {matchProgress}%</Text>
                </View>
              ) : (
                <View>
                  <View style={styles.groupHeaderCard}>
                    <View style={styles.groupHeaderBadge}>
                      <Text style={styles.groupHeaderBadgeText}>MATCH FOUND • 96% OVERLAP</Text>
                    </View>
                    <Text style={styles.groupTitle}>Ride Group #TG-8402</Text>
                    <Text style={styles.groupSub}>2 Co-passengers • ETA Pickup in 4 mins</Text>
                  </View>

                  <View style={styles.timerBanner}>
                    <Text style={styles.timerTitle}>⏱️ GROUP VOTE CLOSES IN</Text>
                    <Text style={styles.timerCount}>{voteTimer}s</Text>
                  </View>

                  <View style={styles.card}>
                    <Text style={styles.cardHeaderTitle}>GROUP MEMBERS</Text>
                    
                    <View style={styles.passengerRow}>
                      <View style={styles.avatar}>
                        <Text style={styles.avatarText}>YOU</Text>
                      </View>
                      <View style={styles.passengerInfo}>
                        <Text style={styles.passengerName}>You (Passenger 1)</Text>
                        <Text style={styles.passengerRoute}>Pickup: Central Sq ➔ Drop: Tech Park</Text>
                      </View>
                      <Text style={styles.fareTag}>₹ 120</Text>
                    </View>

                    <View style={styles.dividerLine} />

                    <View style={styles.passengerRow}>
                      <View style={[styles.avatar, { backgroundColor: '#7C3AED' }]}>
                        <Text style={styles.avatarText}>SK</Text>
                      </View>
                      <View style={styles.passengerInfo}>
                        <Text style={styles.passengerName}>Sarah K. ★ 4.9</Text>
                        <Text style={styles.passengerRoute}>Pickup: 3rd Ave ➔ Drop: Tech Park</Text>
                      </View>
                      <Text style={styles.fareTag}>₹ 110</Text>
                    </View>
                  </View>

                  {!hasVoted ? (
                    <View style={styles.voteBtnRow}>
                      <TouchableOpacity
                        style={styles.acceptVoteBtn}
                        onPress={async () => {
                          setHasVoted(true);
                          await apiService.voteOnGroup('grp_8402', 'ACCEPT');
                          setActiveTab('ride');
                        }}
                      >
                        <Text style={styles.voteBtnText}>ACCEPT GROUP (VOTE YES)</Text>
                      </TouchableOpacity>
                      
                      <TouchableOpacity
                        style={styles.declineVoteBtn}
                        onPress={async () => {
                          await apiService.voteOnGroup('grp_8402', 'DECLINE');
                          setActiveTab('book');
                        }}
                      >
                        <Text style={styles.declineBtnText}>DECLINE</Text>
                      </TouchableOpacity>
                    </View>
                  ) : (
                    <View style={styles.votedSuccessCard}>
                      <Text style={styles.votedText}>✅ Vote Recorded! Assigning Driver...</Text>
                    </View>
                  )}
                </View>
              )}
            </View>
          )}

          {/* TAB 3: LIVE RIDE VIEW */}
          {activeTab === 'ride' && (
            <View style={styles.screenSection}>
              <InteractiveMap
                pickupAddress={pickup}
                dropoffAddress={dropoff}
                pickupLat={pickupLocation.latitude}
                pickupLng={pickupLocation.longitude}
                dropoffLat={dropoffLocation.latitude}
                dropoffLng={dropoffLocation.longitude}
                driverLat={(pickupLocation.latitude + dropoffLocation.latitude) / 2}
                driverLng={(pickupLocation.longitude + dropoffLocation.longitude) / 2}
                isScanning={false}
                driverEtaMins={3}
              />

              <View style={styles.otpCard}>
                <Text style={styles.otpLabel}>SHARE THIS OTP WITH DRIVER TO BOARD</Text>
                <Text style={styles.otpCode}>{rideOtp}</Text>
                <Text style={styles.otpSub}>4-Digit Boarding Verification Code</Text>
              </View>

              <View style={styles.card}>
                <Text style={styles.cardHeaderTitle}>ASSIGNED DRIVER</Text>
                <View style={styles.driverRow}>
                  <View style={styles.driverAvatar}>
                    <Text style={styles.driverAvatarText}>RK</Text>
                  </View>
                  <View style={styles.driverDetails}>
                    <Text style={styles.driverName}>Rajesh Kumar ★ 4.95</Text>
                    <Text style={styles.vehicleText}>White Swift Dzire • MH-12-AB-9842</Text>
                    <Text style={styles.statusText}>Status: EN_ROUTE_TO_PICKUP</Text>
                  </View>
                </View>
              </View>

              <View style={styles.card}>
                <Text style={styles.cardHeaderTitle}>PROPORTIONAL FARE BREAKDOWN</Text>
                <View style={styles.fareRow}>
                  <Text style={styles.fareLabel}>Base Fare (6.2 km)</Text>
                  <Text style={styles.fareVal}>₹ 140.00</Text>
                </View>
                <View style={styles.fareRow}>
                  <Text style={styles.fareLabel}>Shared Group Discount (38%)</Text>
                  <Text style={styles.fareDiscount}>- ₹ 53.20</Text>
                </View>
                <View style={styles.dividerLine} />
                <View style={styles.fareRow}>
                  <Text style={styles.totalFareLabel}>Total Payable</Text>
                  <Text style={styles.totalFareVal}>₹ 98.80</Text>
                </View>
              </View>
            </View>
          )}

          {/* TAB 4: WALLET */}
          {activeTab === 'wallet' && (
            <View style={styles.screenSection}>
              <View style={styles.walletCard}>
                <Text style={styles.walletTitle}>Traveo Digital Wallet</Text>
                <Text style={styles.walletAmount}>₹ 450.00</Text>
                <Text style={styles.walletSub}>Auto-deducted for completed shared rides</Text>
              </View>
            </View>
          )}
        </ScrollView>

        {/* Navigation Bar */}
        <View style={styles.navBar}>
          <TouchableOpacity
            style={[styles.navItem, activeTab === 'book' && styles.navItemActive]}
            onPress={() => setActiveTab('book')}
          >
            <Text style={styles.navIcon}>🚗</Text>
            <Text style={[styles.navText, activeTab === 'book' && styles.navTextActive]}>Book</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeTab === 'matching' && styles.navItemActive]}
            onPress={() => setActiveTab('matching')}
          >
            <Text style={styles.navIcon}>👥</Text>
            <Text style={[styles.navText, activeTab === 'matching' && styles.navTextActive]}>Group</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeTab === 'ride' && styles.navItemActive]}
            onPress={() => setActiveTab('ride')}
          >
            <Text style={styles.navIcon}>📍</Text>
            <Text style={[styles.navText, activeTab === 'ride' && styles.navTextActive]}>Live Ride</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navItem, activeTab === 'wallet' && styles.navItemActive]}
            onPress={() => setActiveTab('wallet')}
          >
            <Text style={styles.navIcon}>💳</Text>
            <Text style={[styles.navText, activeTab === 'wallet' && styles.navTextActive]}>Wallet</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  outerWrapper: {
    flex: 1,
    backgroundColor: '#030712',
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
    backgroundColor: '#0284C7',
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
  walletHeaderBadge: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  walletBalanceText: {
    color: '#38BDF8',
    fontSize: 12,
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
  authCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 12,
  },
  authBadge: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: 'bold',
  },
  authTitle: {
    color: '#F8FAFC',
    fontSize: 22,
    fontWeight: 'bold',
  },
  authSub: {
    color: '#94A3B8',
    fontSize: 12,
  },
  otpBtn: {
    backgroundColor: '#0F172A',
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  otpBtnText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: 'bold',
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 12,
  },
  cardHeaderTitle: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  inputGroup: {
    gap: 4,
  },
  inputIcon: {
    fontSize: 14,
  },
  inputFlex: {
    flex: 1,
  },
  inputLabel: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: 'bold',
  },
  textInput: {
    backgroundColor: '#0F172A',
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '500',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  dividerLine: {
    height: 1,
    backgroundColor: '#334155',
  },
  rideTypeRow: {
    flexDirection: 'row',
    gap: 10,
  },
  rideTypeBox: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1.5,
    borderColor: '#334155',
  },
  rideTypeActive: {
    borderColor: '#38BDF8',
    backgroundColor: '#0C4A6E',
  },
  rideTypeTitle: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  rideTypePrice: {
    color: '#38BDF8',
    fontSize: 15,
    fontWeight: 'bold',
  },
  rideTypeSavings: {
    color: '#4ADE80',
    fontSize: 10,
    marginTop: 2,
  },
  rideTypeSub: {
    color: '#64748B',
    fontSize: 10,
    marginTop: 2,
  },
  seatRow: {
    marginTop: 4,
    gap: 6,
  },
  seatLabel: {
    color: '#94A3B8',
    fontSize: 12,
  },
  seatSelector: {
    flexDirection: 'row',
    gap: 8,
  },
  seatBtn: {
    flex: 1,
    backgroundColor: '#0F172A',
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  vehicleCategoryColumn: {
    gap: 8,
    marginBottom: 12,
  },
  vehicleOptionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 10,
    borderWidth: 1.5,
    borderColor: '#334155',
    gap: 10,
  },
  vehicleOptionSelected: {
    borderColor: '#38BDF8',
    backgroundColor: 'rgba(56, 189, 248, 0.10)',
  },
  vehicleOptionIcon: {
    fontSize: 24,
  },
  vehicleOptionDetails: {
    flex: 1,
  },
  vehicleOptionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  vehicleOptionTitle: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: 'bold',
  },
  vehicleCapacityBadge: {
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  vehicleCapacityBadgeText: {
    color: '#38BDF8',
    fontSize: 9,
    fontWeight: 'bold',
  },
  vehicleOptionSub: {
    color: '#94A3B8',
    fontSize: 10,
    marginTop: 2,
  },
  vehiclePriceColumn: {
    alignItems: 'flex-end',
  },
  vehicleOptionPrice: {
    color: '#38BDF8',
    fontSize: 14,
    fontWeight: 'bold',
  },
  vehicleOptionSharedTag: {
    color: '#22C55E',
    fontSize: 9,
    fontWeight: 'bold',
  },
  seatLabelHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  seatSubLabel: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: 'bold',
  },
  seatBtnActive: {
    backgroundColor: '#0284C7',
    borderColor: '#38BDF8',
  },
  seatBtnText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: 'bold',
  },
  seatBtnTextActive: {
    color: '#FFFFFF',
  },
  primaryBtn: {
    backgroundColor: '#0284C7',
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  matchingSearchCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
    gap: 6,
  },
  radarIcon: {
    fontSize: 32,
  },
  matchingTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: 'bold',
  },
  matchingSub: {
    color: '#94A3B8',
    fontSize: 12,
    textAlign: 'center',
  },
  progressBarBg: {
    width: '100%',
    height: 8,
    backgroundColor: '#0F172A',
    borderRadius: 4,
    overflow: 'hidden',
    marginTop: 8,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#38BDF8',
  },
  progressText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: 'bold',
    marginTop: 2,
  },
  groupHeaderCard: {
    backgroundColor: '#0F172A',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#0284C7',
    marginBottom: 12,
  },
  groupHeaderBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#0C4A6E',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginBottom: 4,
  },
  groupHeaderBadgeText: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: 'bold',
  },
  groupTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: 'bold',
  },
  groupSub: {
    color: '#94A3B8',
    fontSize: 12,
  },
  timerBanner: {
    backgroundColor: '#451A03',
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#F97316',
    marginBottom: 12,
  },
  timerTitle: {
    color: '#FDBA74',
    fontSize: 12,
    fontWeight: 'bold',
  },
  timerCount: {
    color: '#F97316',
    fontSize: 18,
    fontWeight: 'bold',
  },
  passengerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#0284C7',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  passengerInfo: {
    flex: 1,
  },
  passengerName: {
    color: '#F8FAFC',
    fontSize: 13,
    fontWeight: 'bold',
  },
  passengerRoute: {
    color: '#64748B',
    fontSize: 11,
  },
  fareTag: {
    color: '#38BDF8',
    fontSize: 13,
    fontWeight: 'bold',
  },
  voteBtnRow: {
    gap: 8,
    marginTop: 8,
  },
  acceptVoteBtn: {
    backgroundColor: '#16A34A',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  voteBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  declineVoteBtn: {
    backgroundColor: '#0F172A',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  declineBtnText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: 'bold',
  },
  votedSuccessCard: {
    backgroundColor: '#14532D',
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  puneDropdown: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#38BDF8',
    padding: 8,
    marginTop: 6,
    marginBottom: 6,
    gap: 6,
  },
  puneDropdownHeader: {
    color: '#38BDF8',
    fontSize: 9,
    fontWeight: 'bold',
    letterSpacing: 0.5,
    marginBottom: 2,
    marginLeft: 4,
  },
  puneDropdownItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderRadius: 8,
    backgroundColor: '#1E293B',
    gap: 10,
  },
  puneDropdownIcon: {
    fontSize: 16,
  },
  puneDropdownTextCol: {
    flex: 1,
  },
  puneDropdownTitle: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: 'bold',
  },
  puneDropdownArea: {
    color: '#94A3B8',
    fontSize: 10,
  },
  votedText: {
    color: '#86EFAC',
    fontSize: 13,
    fontWeight: 'bold',
  },
  puneTelemetryBanner: {
    backgroundColor: '#0F172A',
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: '#38BDF8',
    alignItems: 'center',
    marginBottom: 10,
  },
  puneTelemetryText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  puneHighlightText: {
    color: '#38BDF8',
    fontWeight: 'bold',
  },
  vehicleFareBreakdown: {
    color: '#64748B',
    fontSize: 9,
    marginTop: 2,
  },
  vehicleSoloStrikethrough: {
    color: '#64748B',
    fontSize: 9,
    textDecorationLine: 'line-through',
  },
  otpCard: {
    backgroundColor: '#0284C7',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
  },
  otpLabel: {
    color: '#E0F2FE',
    fontSize: 10,
    fontWeight: 'bold',
  },
  otpCode: {
    color: '#FFFFFF',
    fontSize: 34,
    fontWeight: 'bold',
    letterSpacing: 6,
    marginVertical: 4,
  },
  otpSub: {
    color: '#BAE6FD',
    fontSize: 11,
  },
  driverRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  driverAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#15803D',
    alignItems: 'center',
    justifyContent: 'center',
  },
  driverAvatarText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  driverDetails: {
    flex: 1,
  },
  driverName: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: 'bold',
  },
  vehicleText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  statusText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: 'bold',
    marginTop: 2,
  },
  fareRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  fareLabel: {
    color: '#94A3B8',
    fontSize: 12,
  },
  fareVal: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: 'bold',
  },
  fareDiscount: {
    color: '#4ADE80',
    fontSize: 12,
    fontWeight: 'bold',
  },
  totalFareLabel: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: 'bold',
  },
  totalFareVal: {
    color: '#38BDF8',
    fontSize: 16,
    fontWeight: 'bold',
  },
  walletCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  walletTitle: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: 'bold',
  },
  walletAmount: {
    color: '#38BDF8',
    fontSize: 36,
    fontWeight: 'bold',
    marginVertical: 4,
  },
  walletSub: {
    color: '#64748B',
    fontSize: 11,
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
    color: '#38BDF8',
  },
});

/**
 * Traveo Pune City Location & Real-Time OpenStreetMap Geocoding Service
 * Constrained strictly to Pune Metropolitan Region & PCMC
 */

export interface PuneLocation {
  name: string;
  area: string;
  latitude: number;
  longitude: number;
  type: 'hub' | 'it_park' | 'station' | 'airport' | 'residential' | 'custom';
}

// 📌 Curated High-Density Pune Popular & Micro Locations Database
export const PUNE_POPULAR_LOCATIONS: PuneLocation[] = [
  // IT & Tech Hubs
  { name: 'Hinjewadi Phase 1 (Quadron Business Park)', area: 'Hinjewadi', latitude: 18.5912, longitude: 73.7389, type: 'it_park' },
  { name: 'EON Free Zone Phase 1 & 2', area: 'Kharadi', latitude: 18.5516, longitude: 73.9530, type: 'it_park' },
  { name: 'Magarpatta Cybercity Tower 4', area: 'Hadapsar', latitude: 18.5158, longitude: 73.9272, type: 'it_park' },
  { name: 'Commerzone IT Park', area: 'Yerwada', latitude: 18.5583, longitude: 73.8784, type: 'it_park' },
  { name: 'Baner Balewadi High Street', area: 'Baner', latitude: 18.5679, longitude: 73.7766, type: 'it_park' },

  // Transit & Hubs
  { name: 'Pune Junction Railway Station', area: 'Shivajinagar', latitude: 18.5289, longitude: 73.8744, type: 'station' },
  { name: 'Pune International Airport (PNQ)', area: 'Lohegaon', latitude: 18.5822, longitude: 73.9197, type: 'airport' },
  { name: 'Swargate MSRTC Central Bus Stand', area: 'Swargate', latitude: 18.5018, longitude: 73.8636, type: 'station' },
  { name: 'Shivajinagar Bus Stand & Metro Station', area: 'Shivajinagar', latitude: 18.5314, longitude: 73.8446, type: 'hub' },
  { name: 'Deccan Gymkhana (FC Road Goodluck Cafe)', area: 'Deccan', latitude: 18.5167, longitude: 73.8413, type: 'hub' },

  // Key West Pune Areas
  { name: 'Kothrud (Chandani Chowk Flyover)', area: 'Kothrud', latitude: 18.5074, longitude: 73.7925, type: 'residential' },
  { name: 'Aundh (Parihar Chowk)', area: 'Aundh', latitude: 18.5602, longitude: 73.8077, type: 'residential' },
  { name: 'Wakad (Ginger Hotel Chowk)', area: 'Wakad', latitude: 18.5987, longitude: 73.7644, type: 'residential' },
  { name: 'Bavdhan (Chandani Chowk)', area: 'Bavdhan', latitude: 18.5100, longitude: 73.7700, type: 'residential' },
  { name: 'Karve Nagar (Rajaram Bridge)', area: 'Karve Nagar', latitude: 18.4900, longitude: 73.8200, type: 'residential' },

  // Key East & South Pune Areas
  { name: 'Viman Nagar (Phoenix Marketcity)', area: 'Viman Nagar', latitude: 18.5622, longitude: 73.9167, type: 'hub' },
  { name: 'Koregaon Park (Lane 6 Starbucks)', area: 'Koregaon Park', latitude: 18.5362, longitude: 73.8940, type: 'hub' },
  { name: 'Hadapsar (Gadital Chowk)', area: 'Hadapsar', latitude: 18.5028, longitude: 73.9275, type: 'residential' },
  { name: 'Katraj Snake Park & Zoo Chowk', area: 'Katraj', latitude: 18.4485, longitude: 73.8587, type: 'residential' },
  { name: 'Kondhwa (NIBM Road Junction)', area: 'Kondhwa', latitude: 18.4720, longitude: 73.8920, type: 'residential' },

  // PCMC Region
  { name: 'Pimpri Chowk & Metro Station', area: 'Pimpri', latitude: 18.6278, longitude: 73.8009, type: 'hub' },
  { name: 'Chinchwad Railway Station', area: 'Chinchwad', latitude: 18.6355, longitude: 73.7922, type: 'station' },
  { name: 'Nigdi Bhakti Shakti Chowk', area: 'Nigdi', latitude: 18.6575, longitude: 73.7744, type: 'hub' },
];

/**
 * Real-Time OpenStreetMap Nominatim Geocoding API
 * Constrained strictly to Pune Metropolitan Bounding Box
 */
export async function searchPuneLocations(query: string): Promise<PuneLocation[]> {
  if (!query || query.trim().length < 2) {
    return PUNE_POPULAR_LOCATIONS.slice(0, 6);
  }

  const cleanQuery = query.trim();
  
  // First match against local curated Pune database
  const localMatches = PUNE_POPULAR_LOCATIONS.filter(
    (loc) =>
      loc.name.toLowerCase().includes(cleanQuery.toLowerCase()) ||
      loc.area.toLowerCase().includes(cleanQuery.toLowerCase())
  );

  try {
    // Query OpenStreetMap Nominatim API bounded strictly to Pune (viewbox: 73.65,18.35,74.05,18.75)
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
      cleanQuery + ', Pune, Maharashtra, India'
    )}&viewbox=73.65,18.35,74.05,18.75&bounded=1&limit=6`;

    const res = await fetch(url, {
      headers: {
        'Accept-Language': 'en',
        'User-Agent': 'Traveo-Pune-RideSharing-App',
      },
    });

    if (!res.ok) {
      return localMatches.length > 0 ? localMatches : PUNE_POPULAR_LOCATIONS.slice(0, 6);
    }

    const data = await res.json();
    const osmResults: PuneLocation[] = data.map((item: any) => ({
      name: item.display_name.split(',')[0] + ', ' + (item.display_name.split(',')[1] || 'Pune'),
      area: item.display_name.split(',')[1]?.trim() || 'Pune',
      latitude: parseFloat(item.lat),
      longitude: parseFloat(item.lon),
      type: 'custom',
    }));

    // Combine local curated matches with live OSM Geocoding results
    const combined = [...localMatches, ...osmResults];
    // Deduplicate by name
    const unique = Array.from(new Map(combined.map((item) => [item.name, item])).values());
    return unique.slice(0, 6);
  } catch (e) {
    console.warn('Pune OSM Nominatim Geocoding fallback to curated list:', e);
    return localMatches.length > 0 ? localMatches : PUNE_POPULAR_LOCATIONS.slice(0, 6);
  }
}

/**
 * Haversine distance calculation in kilometers between two GPS coordinates
 */
export function calculateHaversineDistanceKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  return Math.max(0.5, Math.round(distance * 10) / 10); // Minimum 0.5 km
}

export interface PuneFareDetails {
  vehicleCategory: 'auto_rickshaw' | 'sedan_4_seater' | 'suv_6_8_seater';
  vehicleName: string;
  distanceKm: number;
  estimatedMinutes: number;
  baseFare: number;
  perKmRate: number;
  soloFare: number;
  sharedFare: number;
  savingsAmount: number;
  savingsPercentage: number;
}

/**
 * Uber/Rapido Pune Rate Card Calculator
 * Auto Rickshaw: ₹30 Base (includes 1.5 km) + ₹15/km
 * 4-Seater Sedan: ₹50 Base (includes 2.0 km) + ₹18/km
 * 6-8 Seater SUV: ₹90 Base (includes 2.0 km) + ₹25/km
 */
export function calculatePunePerKmFare(
  category: 'auto_rickshaw' | 'sedan_4_seater' | 'suv_6_8_seater',
  distanceKm: number,
  seats: number = 1
): PuneFareDetails {
  let baseFare = 50;
  let minKm = 2.0;
  let perKmRate = 18;
  let name = '4-Seater Sedan';

  if (category === 'auto_rickshaw') {
    baseFare = 30;
    minKm = 1.5;
    perKmRate = 15;
    name = 'Auto Rickshaw';
  } else if (category === 'suv_6_8_seater') {
    baseFare = 90;
    minKm = 2.0;
    perKmRate = 25;
    name = '6-8 Seater SUV';
  }

  const extraKm = Math.max(0, distanceKm - minKm);
  const rawSoloFare = Math.round(baseFare + extraKm * perKmRate);

  // Smart Shared Discount (35% off for 1 seat, 20% off for 2 seats)
  let sharedDiscountRatio = 0.65; // 35% discount
  if (seats === 2) sharedDiscountRatio = 0.80;
  if (seats >= 3) sharedDiscountRatio = 0.95;

  const sharedFare = Math.round(rawSoloFare * sharedDiscountRatio);
  const savingsAmount = rawSoloFare - sharedFare;
  const savingsPercentage = Math.round((savingsAmount / rawSoloFare) * 100);

  // Estimated driving time in Pune traffic (average 22 km/h city speed)
  const estimatedMinutes = Math.max(5, Math.round((distanceKm / 22) * 60));

  return {
    vehicleCategory: category,
    vehicleName: name,
    distanceKm,
    estimatedMinutes,
    baseFare,
    perKmRate,
    soloFare: rawSoloFare,
    sharedFare,
    savingsAmount,
    savingsPercentage,
  };
}

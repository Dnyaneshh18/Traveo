import React, { useEffect, useRef } from 'react';
import { StyleSheet, View, Text } from 'react-native';

interface InteractiveMapProps {
  pickupAddress?: string;
  dropoffAddress?: string;
  pickupLat?: number;
  pickupLng?: number;
  dropoffLat?: number;
  dropoffLng?: number;
  driverLat?: number;
  driverLng?: number;
  isScanning?: boolean;
  searchRadiusKm?: number;
  driverEtaMins?: number;
}

export const InteractiveMap: React.FC<InteractiveMapProps> = ({
  pickupAddress = 'Central Square, Downtown',
  dropoffAddress = 'Tech Park Tower B',
  pickupLat = 18.5204,
  pickupLng = 73.8567,
  dropoffLat = 18.5529,
  dropoffLng = 73.8796,
  driverLat = 18.5250,
  driverLng = 73.8600,
  isScanning = false,
  searchRadiusKm = 2.5,
  driverEtaMins = 3,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Generate Leaflet HTML document with CartoDB Dark OpenStreetMap Tiles
  const mapHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <style>
        html, body, #map {
          width: 100%;
          height: 100%;
          margin: 0;
          padding: 0;
          background-color: #020617;
        }
        .leaflet-container {
          background-color: #020617 !important;
        }
        .custom-pin {
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: system-ui, -apple-system, sans-serif;
          font-weight: bold;
          font-size: 11px;
          color: white;
          padding: 3px 8px;
          border-radius: 12px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5);
          white-space: nowrap;
        }
        .pickup-pin {
          background-color: #0F172A;
          border: 1.5px solid #22C55E;
          color: #22C55E;
        }
        .dropoff-pin {
          background-color: #0F172A;
          border: 1.5px solid #EF4444;
          color: #EF4444;
        }
        .driver-pin {
          background-color: #15803D;
          border: 1.5px solid #38BDF8;
          color: #FFFFFF;
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.7); }
          70% { box-shadow: 0 0 0 10px rgba(56, 189, 248, 0); }
          100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
        }
      </style>
    </head>
    <body>
      <div id="map"></div>
      <script>
        // Initialize OpenStreetMap Leaflet map centered between pickup and dropoff
        const map = L.map('map', {
          zoomControl: false,
          attributionControl: false
        }).setView([${(pickupLat + dropoffLat) / 2}, ${(pickupLng + dropoffLng) / 2}], 13);

        // Add CartoDB Dark Matter OpenStreetMap Tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          maxZoom: 19,
          subdomains: 'abcd'
        }).addTo(map);

        // Pickup Marker
        const pickupIcon = L.divIcon({
          className: '',
          html: '<div class="custom-pin pickup-pin">🟢 ${pickupAddress.split(',')[0]}</div>',
          iconSize: [120, 24],
          iconAnchor: [60, 12]
        });
        L.marker([${pickupLat}, ${pickupLng}], { icon: pickupIcon }).addTo(map);

        // Dropoff Marker
        const dropoffIcon = L.divIcon({
          className: '',
          html: '<div class="custom-pin dropoff-pin">🔴 ${dropoffAddress.split(',')[0]}</div>',
          iconSize: [120, 24],
          iconAnchor: [60, 12]
        });
        L.marker([${dropoffLat}, ${dropoffLng}], { icon: dropoffIcon }).addTo(map);

        // Real-time Driver Vehicle Marker
        const driverIcon = L.divIcon({
          className: '',
          html: '<div class="custom-pin driver-pin">🚘 Driver (${driverEtaMins}m)</div>',
          iconSize: [110, 24],
          iconAnchor: [55, 12]
        });
        L.marker([${driverLat}, ${driverLng}], { icon: driverIcon }).addTo(map);

        // Route Polyline connecting Pickup to Dropoff
        const routeLine = L.polyline([
          [${pickupLat}, ${pickupLng}],
          [${driverLat}, ${driverLng}],
          [${dropoffLat}, ${dropoffLng}]
        ], {
          color: '#38BDF8',
          weight: 3,
          dashArray: '6, 8',
          opacity: 0.8
        }).addTo(map);

        ${isScanning ? `
        // Radar Search Radius Circle
        L.circle([${pickupLat}, ${pickupLng}], {
          color: '#38BDF8',
          fillColor: '#38BDF8',
          fillOpacity: 0.15,
          radius: ${searchRadiusKm * 1000}
        }).addTo(map);
        ` : ''}

        // Auto-fit bounds
        map.fitBounds([
          [${pickupLat}, ${pickupLng}],
          [${dropoffLat}, ${dropoffLng}],
          [${driverLat}, ${driverLng}]
        ], { padding: [30, 30] });
      </script>
    </body>
    </html>
  `;

  return (
    <View style={styles.mapContainer}>
      <iframe
        key={`${pickupLat}-${pickupLng}-${dropoffLat}-${dropoffLng}-${driverLat}-${driverLng}-${isScanning}-${searchRadiusKm}`}
        title="OpenStreetMap Live Tracking"
        srcDoc={mapHtml}
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          borderRadius: '16px',
        }}
      />

      {/* Live Status Overlay Tag */}
      <View style={styles.mapFooterTag}>
        <Text style={styles.footerTagText}>
          {isScanning
            ? `📡 AI SEARCH RADIUS: ${searchRadiusKm} KM`
            : `📍 OPENSTREETMAP REAL-TIME GPS`}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  mapContainer: {
    width: '100%',
    height: 220,
    backgroundColor: '#020617',
    borderRadius: 16,
    overflow: 'hidden',
    position: 'relative',
    borderWidth: 1,
    borderColor: '#1E293B',
  },
  mapFooterTag: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    backgroundColor: 'rgba(15, 23, 42, 0.90)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#38BDF8',
    pointerEvents: 'none',
  },
  footerTagText: {
    color: '#38BDF8',
    fontSize: 10,
    fontWeight: 'bold',
  },
});

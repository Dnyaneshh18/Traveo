import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors } from '@traveo/shared';
import type { MapMarker } from './types';

const KIND_COLOR: Record<MapMarker['kind'], string> = {
  driver: colors.driver,
  rider: colors.rider,
  me: colors.primary,
  pickup: colors.pickup,
  drop: colors.drop,
  campus: colors.campus,
  stop: colors.text,
};

const KIND_GLYPH: Record<MapMarker['kind'], string> = {
  driver: '🚕',
  rider: '🧑‍🎓',
  me: '●',
  pickup: '▲',
  drop: '■',
  campus: '🎓',
  stop: '•',
};

/** Marker rendered as a native RN view (used by Mappls MarkerView); web builds its own HTML. */
export function MarkerGlyph({ marker }: { marker: MapMarker }) {
  const color = marker.color ?? KIND_COLOR[marker.kind];
  if (marker.kind === 'driver') {
    return (
      <View style={[styles.driver, { transform: [{ rotate: `${marker.heading ?? 0}deg` }] }]}>
        <View style={[styles.driverBody, { backgroundColor: color }]}>
          <Text style={styles.driverGlyph}>🚗</Text>
        </View>
        <View style={[styles.arrow, { borderBottomColor: color }]} />
      </View>
    );
  }
  if (marker.kind === 'me') {
    return (
      <View style={styles.meOuter}>
        <View style={[styles.meInner, { backgroundColor: color }]} />
      </View>
    );
  }
  return (
    <View style={styles.pinWrap}>
      <View style={[styles.pin, { backgroundColor: color }]}>
        <Text style={styles.pinTxt}>{marker.label ?? KIND_GLYPH[marker.kind]}</Text>
      </View>
      <View style={[styles.pinTail, { borderTopColor: color }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  driver: { alignItems: 'center', width: 44, height: 52 },
  arrow: { width: 0, height: 0, borderLeftWidth: 7, borderRightWidth: 7, borderBottomWidth: 12, borderLeftColor: 'transparent', borderRightColor: 'transparent', position: 'absolute', top: -6 },
  driverBody: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: '#fff', marginTop: 4, shadowColor: '#000', shadowOpacity: 0.3, shadowRadius: 4, elevation: 4 },
  driverGlyph: { fontSize: 16 },
  meOuter: { width: 26, height: 26, borderRadius: 13, backgroundColor: 'rgba(79,70,229,0.2)', alignItems: 'center', justifyContent: 'center' },
  meInner: { width: 14, height: 14, borderRadius: 7, borderWidth: 2.5, borderColor: '#fff' },
  pinWrap: { alignItems: 'center', width: 40, height: 48 },
  pin: { minWidth: 32, height: 32, paddingHorizontal: 6, borderRadius: 16, alignItems: 'center', justifyContent: 'center', borderWidth: 2.5, borderColor: '#fff', shadowColor: '#000', shadowOpacity: 0.25, shadowRadius: 4, elevation: 4 },
  pinTxt: { color: '#fff', fontWeight: '800', fontSize: 13 },
  pinTail: { width: 0, height: 0, borderLeftWidth: 6, borderRightWidth: 6, borderTopWidth: 9, borderLeftColor: 'transparent', borderRightColor: 'transparent', marginTop: -2 },
});

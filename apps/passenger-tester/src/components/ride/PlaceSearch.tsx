import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, TextInput, View } from 'react-native';
import { colors, radii, spacing, typography, type LatLng, type Place, type PlaceSuggestion } from '@traveo/shared';
import { api } from '@/lib/api';
import { getCurrentFix, Body, Small, SmallBold } from '@traveo/mobile-ui';

interface Props {
  label: string;
  value: Place | null;
  onChange: (place: Place | null) => void;
  near?: LatLng | null;
  placeholder?: string;
  presets?: Place[]; // e.g. campus
  allowCurrentLocation?: boolean;
  autoFocus?: boolean;
  accent?: string;
}

export function PlaceSearch({ label, value, onChange, near, placeholder, presets = [], allowCurrentLocation = true, autoFocus, accent = colors.primary }: Props) {
  const [query, setQuery] = useState(value?.name || value?.address || '');
  const [results, setResults] = useState<PlaceSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setQuery(value?.name || value?.address || '');
  }, [value?.address, value?.name]);

  useEffect(() => {
    if (!open) return;
    if (timer.current) clearTimeout(timer.current);
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    timer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.maps.autosuggest(query.trim(), near ?? undefined);
        setResults(res.data.filter((r) => r.lat !== null && r.lng !== null));
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 280);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [query, open, near?.lat, near?.lng]);

  const choose = (p: Place) => {
    onChange(p);
    setQuery(p.name || p.address);
    setOpen(false);
  };

  const useCurrent = async () => {
    setLoading(true);
    const fix = await getCurrentFix();
    if (fix) {
      try {
        const geo = await api.maps.reverseGeocode(fix.lat, fix.lng);
        choose({ lat: fix.lat, lng: fix.lng, address: geo.data.address, name: 'Current location' });
      } catch {
        choose({ lat: fix.lat, lng: fix.lng, address: `${fix.lat.toFixed(5)}, ${fix.lng.toFixed(5)}`, name: 'Current location' });
      }
    }
    setLoading(false);
  };

  return (
    <View style={{ zIndex: open ? 20 : 1 }}>
      <SmallBold color={colors.textSecondary} style={{ marginBottom: 6 }}>{label}</SmallBold>
      <View style={[styles.inputWrap, { borderColor: open ? accent : colors.border }]}>
        <View style={[styles.dot, { backgroundColor: accent }]} />
        <TextInput
          value={query}
          onChangeText={(t) => {
            setQuery(t);
            setOpen(true);
            if (value) onChange(null);
          }}
          onFocus={() => setOpen(true)}
          placeholder={placeholder ?? 'Search a place'}
          placeholderTextColor={colors.textMuted}
          style={styles.input}
          autoFocus={autoFocus}
          autoCorrect={false}
        />
        {loading ? <ActivityIndicator size="small" color={accent} /> : null}
        {query.length > 0 ? (
          <Pressable onPress={() => { setQuery(''); onChange(null); setResults([]); setOpen(true); }} hitSlop={8}>
            <Small color={colors.textMuted}>✕</Small>
          </Pressable>
        ) : null}
      </View>

      {open ? (
        <View style={styles.dropdown}>
          {presets.map((p) => (
            <Pressable key={`preset-${p.address}`} onPress={() => choose(p)} style={styles.row}>
              <Small color={colors.primary}>🎓</Small>
              <View style={{ flex: 1 }}>
                <Body numberOfLines={1}>{p.name || p.address}</Body>
                <Small numberOfLines={1}>{p.address}</Small>
              </View>
            </Pressable>
          ))}
          {allowCurrentLocation ? (
            <Pressable onPress={useCurrent} style={styles.row}>
              <Small color={colors.primary}>◎</Small>
              <Body color={colors.primary}>Use my current location</Body>
            </Pressable>
          ) : null}
          <FlatList
            data={results}
            keyExtractor={(item, i) => `${item.place_id ?? item.name}-${i}`}
            keyboardShouldPersistTaps="handled"
            style={{ maxHeight: 240 }}
            renderItem={({ item }) => (
              <Pressable onPress={() => choose({ lat: item.lat!, lng: item.lng!, address: item.address, name: item.name })} style={styles.row}>
                <Small color={colors.textMuted}>📍</Small>
                <View style={{ flex: 1 }}>
                  <Body numberOfLines={1}>{item.name}</Body>
                  <Small numberOfLines={1}>{item.address}</Small>
                </View>
                {item.distance_km != null ? <Small>{item.distance_km} km</Small> : null}
              </Pressable>
            )}
            ListEmptyComponent={query.trim().length >= 2 && !loading ? <Small style={{ padding: spacing.md }}>No places found</Small> : null}
          />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  inputWrap: { flexDirection: 'row', alignItems: 'center', gap: 10, borderWidth: 1.5, borderRadius: radii.md, backgroundColor: colors.surface, paddingHorizontal: 12 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  input: { flex: 1, paddingVertical: 12, ...typography.body, color: colors.text },
  dropdown: { marginTop: 6, backgroundColor: colors.surface, borderRadius: radii.md, borderWidth: 1, borderColor: colors.border, overflow: 'hidden' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 12, paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
});

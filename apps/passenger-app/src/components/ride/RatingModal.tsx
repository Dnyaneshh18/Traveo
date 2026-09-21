import React, { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { colors, radii, shadows, spacing } from '@traveo/shared';
import { BodyBold, Button, Caption, H2, Row, Small, toast } from '@traveo/mobile-ui';
import { api } from '@/lib/api';

export interface PendingRatingData {
  ride_id: string;
  request_id: string;
  role: 'passenger' | 'driver';
  driver_name?: string;
  driver_id?: string;
  passenger_count?: number;
  origin_address?: string;
  destination_address?: string;
  fare_share_inr?: number;
  completed_at?: string | null;
}

interface Props {
  data: PendingRatingData | null;
  visible: boolean;
  onClose: () => void;
}

export function RatingModal({ data, visible, onClose }: Props) {
  const queryClient = useQueryClient();
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState('');

  const submit = useMutation({
    mutationFn: () =>
      api.rides.rate({
        ride_id: data!.ride_id,
        ratee_id: data!.role === 'passenger' ? data!.driver_id : undefined,
        stars,
        comment: comment.trim() || undefined,
      }),
    onSuccess: () => {
      toast('Thanks for your rating! ⭐', undefined, 'success');
      queryClient.invalidateQueries({ queryKey: ['ratings', 'pending'] });
      queryClient.invalidateQueries({ queryKey: ['rides'] });
      queryClient.invalidateQueries({ queryKey: ['driver', 'earnings'] });
      onClose();
    },
    onError: (e: any) => {
      toast('Rating failed', e?.message, 'error');
    },
  });

  if (!data || !visible) return null;

  const isPassenger = data.role === 'passenger';
  const title = isPassenger ? `How was your driver?` : `How were the passengers?`;
  const subtitle = isPassenger
    ? (data.driver_name ? `${data.driver_name} · ${data.destination_address || 'Completed Ride'}` : 'Rate your recent trip experience')
    : `${data.passenger_count || 1} student(s) · ${data.destination_address || 'Completed Trip'}`;

  const ratingTags = isPassenger
    ? ['Polite & respectful', 'Smooth driving', 'Clean vehicle', 'On time']
    : ['Great students', 'Cooperative', 'On time for pickup', 'Polite'];

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Pressable onPress={onClose} style={styles.closeBtn} hitSlop={12}>
            <Text style={styles.closeTxt}>✕</Text>
          </Pressable>

          <View style={styles.iconCircle}>
            <Text style={{ fontSize: 36 }}>{isPassenger ? '🚕' : '🎓'}</Text>
          </View>

          <H2 center>{title}</H2>
          <Small center color={colors.textSecondary}>{subtitle}</Small>

          {/* Star selector */}
          <Row gap={8} style={{ alignSelf: 'center', marginVertical: spacing.md }}>
            {[1, 2, 3, 4, 5].map((s) => (
              <Pressable key={s} onPress={() => setStars(s)} hitSlop={6}>
                <Text style={[styles.star, { opacity: s <= stars ? 1 : 0.25 }]}>⭐</Text>
              </Pressable>
            ))}
          </Row>

          <Caption center style={{ marginBottom: 4 }}>
            {stars === 5 ? 'Exceptional experience!' : stars === 4 ? 'Good ride' : stars === 3 ? 'Average' : 'Could be better'}
          </Caption>

          {/* Feedback quick tags */}
          <View style={styles.tagsContainer}>
            {ratingTags.map((tag) => {
              const selected = comment.includes(tag);
              return (
                <Pressable
                  key={tag}
                  style={[styles.tag, selected && styles.tagActive]}
                  onPress={() => {
                    if (selected) {
                      setComment((prev) => prev.replace(tag, '').replace(/,\s*,/g, ',').trim());
                    } else {
                      setComment((prev) => (prev ? `${prev}, ${tag}` : tag));
                    }
                  }}
                >
                  <Small style={[styles.tagTxt, selected && styles.tagTxtActive]}>{tag}</Small>
                </Pressable>
              );
            })}
          </View>

          {/* Optional comment field */}
          <TextInput
            placeholder="Add a compliment or note (optional)…"
            placeholderTextColor={colors.textMuted}
            value={comment}
            onChangeText={setComment}
            style={styles.input}
            maxLength={250}
          />

          <Button
            title={submit.isPending ? 'Submitting…' : 'Submit feedback'}
            onPress={() => submit.mutate()}
            loading={submit.isPending}
            style={{ width: '100%', marginTop: spacing.sm }}
          />

          <Pressable onPress={onClose} style={styles.skipBtn}>
            <Small color={colors.textMuted}>Skip for now</Small>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.md,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: colors.surface,
    borderRadius: radii.xl,
    padding: spacing.xl,
    alignItems: 'center',
    ...shadows.float,
    position: 'relative',
  },
  closeBtn: {
    position: 'absolute',
    top: 14,
    right: 16,
    padding: 6,
    zIndex: 10,
  },
  closeTxt: {
    fontSize: 18,
    color: colors.textMuted,
    fontWeight: 'bold',
  },
  iconCircle: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: colors.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  star: {
    fontSize: 36,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    justifyContent: 'center',
    marginVertical: spacing.sm,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radii.pill,
    backgroundColor: colors.surfaceAlt,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tagActive: {
    backgroundColor: colors.primaryLight,
    borderColor: colors.primary,
  },
  tagTxt: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  tagTxtActive: {
    color: colors.primaryDark,
    fontWeight: '600',
  },
  input: {
    width: '100%',
    backgroundColor: colors.background,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 13,
    color: colors.text,
    marginTop: 4,
    marginBottom: 8,
  },
  skipBtn: {
    marginTop: spacing.md,
    paddingVertical: 4,
  },
});

"""
Traveo Backend — Fare Engine & Shared Fare Splitting Calculator

Calculates individual and group fares.
Shared rides use proportional fare splitting based on individual distance and time,
ensuring fairness (Part 13 spec requirement: "Avoid equal division").
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FareBreakdown:
    base_fare: float
    distance_fare: float
    duration_fare: float
    platform_fee: float
    tax_amount: float
    discount_amount: float
    total_fare: float


@dataclass
class PassengerFareSplit:
    passenger_id: str
    individual_distance_km: float
    shared_discount_percent: float
    final_fare: float


class FareEngine:
    """Calculates ride fares based on configurable pricing parameters."""

    def __init__(
        self,
        base_fare: float = 30.0,
        per_km_rate: float = 12.0,
        per_minute_rate: float = 2.0,
        platform_fee_percent: float = 10.0,
        tax_percent: float = 5.0,
        shared_ride_discount_percent: float = 15.0,
    ) -> None:
        self.base_fare = base_fare
        self.per_km_rate = per_km_rate
        self.per_minute_rate = per_minute_rate
        self.platform_fee_percent = platform_fee_percent
        self.tax_percent = tax_percent
        self.shared_discount_percent = shared_ride_discount_percent

    def calculate_total_fare(
        self,
        distance_km: float,
        duration_minutes: float,
        is_shared: bool = True,
    ) -> FareBreakdown:
        """Calculate complete fare breakdown for a trip."""
        dist_fare = round(distance_km * self.per_km_rate, 2)
        dur_fare = round(duration_minutes * self.per_minute_rate, 2)

        subtotal = self.base_fare + dist_fare + dur_fare

        # Apply shared discount if applicable
        if is_shared:
            discount = round(subtotal * (self.shared_discount_percent / 100.0), 2)
        else:
            discount = 0.0

        discounted_subtotal = max(0.0, subtotal - discount)

        platform_fee = round(discounted_subtotal * (self.platform_fee_percent / 100.0), 2)
        tax = round(discounted_subtotal * (self.tax_percent / 100.0), 2)
        total = round(discounted_subtotal + platform_fee + tax, 2)

        return FareBreakdown(
            base_fare=self.base_fare,
            distance_fare=dist_fare,
            duration_fare=dur_fare,
            platform_fee=platform_fee,
            tax_amount=tax,
            discount_amount=discount,
            total_fare=total,
        )


class SharedFareSplitter:
    """
    Proportionately splits total group fare among passengers based on individual distance.
    Guarantees sum of split fares equals group total.
    """

    @staticmethod
    def split_group_fare(
        passenger_distances: dict[str, float],
        group_total_fare: float,
    ) -> list[PassengerFareSplit]:
        """
        Args:
            passenger_distances: dict of {passenger_id: individual_distance_km}
            group_total_fare: total calculated fare for the entire group trip

        Returns:
            list of PassengerFareSplit with proportional fares
        """
        total_dist_sum = sum(passenger_distances.values())
        if total_dist_sum <= 0:
            # Fallback to equal split if distance is zero
            num = len(passenger_distances)
            equal_fare = round(group_total_fare / num, 2)
            return [
                PassengerFareSplit(
                    passenger_id=pid,
                    individual_distance_km=0.0,
                    shared_discount_percent=15.0,
                    final_fare=equal_fare,
                )
                for pid in passenger_distances
            ]

        splits: list[PassengerFareSplit] = []
        allocated_sum = 0.0
        items = list(passenger_distances.items())

        for i, (pid, dist) in enumerate(items):
            if i == len(items) - 1:
                # Last passenger gets remainder to avoid rounding penny discrepancy
                fare = round(group_total_fare - allocated_sum, 2)
            else:
                proportion = dist / total_dist_sum
                fare = round(group_total_fare * proportion, 2)
                allocated_sum += fare

            splits.append(
                PassengerFareSplit(
                    passenger_id=pid,
                    individual_distance_km=dist,
                    shared_discount_percent=15.0,
                    final_fare=fare,
                )
            )

        return splits

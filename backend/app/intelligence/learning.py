"""
Traveo Ride Intelligence Engine — Dynamic Radius Expansion & AI Learning Feedback

Implements dynamic search radius expansion and historical learning feedback recorder
per Part 13 specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import structlog

logger = structlog.get_logger(__name__)


def calculate_dynamic_search_radius(
    elapsed_waiting_seconds: float,
    initial_radius_km: float = 2.0,
    max_radius_km: float = 5.0,
    expansion_step_km: float = 0.5,
    step_interval_seconds: float = 30.0,
) -> float:
    """
    Calculate dynamic search radius based on passenger wait duration.
    As time progresses without finding a match, the search radius expands
    gradually up to max_radius_km.
    """
    if elapsed_waiting_seconds <= 0:
        return initial_radius_km

    steps = int(elapsed_waiting_seconds // step_interval_seconds)
    expanded = initial_radius_km + (steps * expansion_step_km)
    return round(min(max_radius_km, expanded), 2)


@dataclass
class MatchOutcomeRecord:
    match_id: str
    request_a_id: str
    request_b_id: str
    score: float
    outcome: str  # "accepted", "rejected", "completed", "cancelled", "no_show"
    actual_detour_km: float | None = None
    passenger_rating: float | None = None
    timestamp: datetime = datetime.now(UTC)


class AILearningRecorder:
    """
    Records match outcomes for future offline AI model training.
    Does not make real-time decisions — logs structured events for analytics.
    """

    @staticmethod
    def record_outcome(outcome_record: MatchOutcomeRecord) -> None:
        logger.info(
            "ai_match_feedback_logged",
            match_id=outcome_record.match_id,
            request_a=outcome_record.request_a_id,
            request_b=outcome_record.request_b_id,
            matching_score=outcome_record.score,
            outcome=outcome_record.outcome,
            actual_detour_km=outcome_record.actual_detour_km,
            passenger_rating=outcome_record.passenger_rating,
        )

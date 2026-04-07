"""Domain objects for the Wave 2B Context Gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now


class GateVerdict(StrEnum):
    """Formal gate decision vocabulary for the context admission barrier."""

    ADMITTED = "admitted"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class GateReason(StrEnum):
    """Explicit admission-failure taxonomy for the Wave 2B gate."""

    CONTEXT_NOT_READY = "context_not_ready"
    REQUIRED_TIMEFRAME_MISSING = "required_timeframe_missing"
    REQUIRED_COMPONENT_UNAVAILABLE = "required_component_unavailable"
    REQUIRED_TIMEFRAME_NOT_CLOSED = "required_timeframe_not_closed"
    DATA_GAP_DETECTED = "data_gap_detected"
    LOOKAHEAD_VIOLATION = "lookahead_violation"
    STALE_CONTEXT = "stale_context"
    TIMEFRAME_NOT_READY = "timeframe_not_ready"
    WARMUP_NOT_REACHED = "warmup_not_reached"


@dataclass(frozen=True, slots=True)
class GateOutcome:
    """Formal gate outcome for the current timeframe context."""

    outcome_id: str
    verdict: GateVerdict
    reason: GateReason | None
    bars_seen: int
    warmup_required: int
    checked_at: datetime

    def __post_init__(self) -> None:
        require_utc_datetime(self.checked_at, "checked_at")

    @classmethod
    def create(
        cls,
        *,
        verdict: GateVerdict,
        reason: GateReason | None,
        bars_seen: int,
        warmup_required: int,
    ) -> "GateOutcome":
        """Build a formal gate outcome with a generated identity."""

        if verdict in (GateVerdict.DEFERRED, GateVerdict.REJECTED) and reason is None:
            raise ValueError("reason must be provided for DEFERRED and REJECTED outcomes")

        return cls(
            outcome_id=new_internal_id("gate"),
            verdict=verdict,
            reason=reason,
            bars_seen=bars_seen,
            warmup_required=warmup_required,
            checked_at=utc_now(),
        )

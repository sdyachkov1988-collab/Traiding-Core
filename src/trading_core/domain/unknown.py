"""Unknown-state and safe-recovery domain objects for Wave 2C."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now


class UnknownStateKind(StrEnum):
    """Formal classes of unknown state recognized by the core."""

    UNKNOWN_ORDER_STATE = "unknown_order_state"
    UNKNOWN_POSITION_STATE = "unknown_position_state"
    STALE_CONTEXT = "stale_context"
    INCOMPLETE_EXTERNAL_CONFIRMATION = "incomplete_external_confirmation"
    RECONCILIATION_INSUFFICIENT = "reconciliation_insufficient"
    RECONCILIATION_CONFLICT = "reconciliation_conflict"


class SystemMode(StrEnum):
    """System operating mode under normal and failure-path conditions."""

    NORMAL = "normal"
    READ_ONLY = "read_only"
    SAFE_MODE = "safe_mode"
    FROZEN = "frozen"


@dataclass(frozen=True, slots=True)
class UnknownStateRecord:
    """Formal record describing a recognized unknown-state condition."""

    record_id: str
    kind: UnknownStateKind
    reason: str
    detected_at: datetime
    instrument_id: str | None = None
    order_intent_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.detected_at, "detected_at")

    @classmethod
    def create(
        cls,
        *,
        kind: UnknownStateKind,
        reason: str,
        instrument_id: str | None = None,
        order_intent_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "UnknownStateRecord":
        """Build a formal unknown-state record."""

        return cls(
            record_id=new_internal_id("unknown"),
            kind=kind,
            reason=reason,
            detected_at=utc_now(),
            instrument_id=instrument_id,
            order_intent_id=order_intent_id,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class SystemModeTransition:
    """Formal transition between system modes under failure-path semantics."""

    transition_id: str
    from_mode: SystemMode
    to_mode: SystemMode
    reason: str
    unknown_state: UnknownStateRecord | None
    transitioned_at: datetime

    def __post_init__(self) -> None:
        require_utc_datetime(self.transitioned_at, "transitioned_at")

    @classmethod
    def create(
        cls,
        *,
        from_mode: SystemMode,
        to_mode: SystemMode,
        reason: str,
        unknown_state: UnknownStateRecord | None = None,
    ) -> "SystemModeTransition":
        """Build a formal mode transition record."""

        return cls(
            transition_id=new_internal_id("transition"),
            from_mode=from_mode,
            to_mode=to_mode,
            reason=reason,
            unknown_state=unknown_state,
            transitioned_at=utc_now(),
        )

"""Domain contracts for the Wave 2A MTF foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from trading_core.domain.common import new_internal_id, utc_now


@dataclass(frozen=True, slots=True)
class ClosedBar:
    """A canonical closed bar used by the MTF foundation layer."""

    timeframe: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    bar_time: datetime
    is_closed: bool = True


@dataclass(frozen=True, slots=True)
class TimeframeSyncEvent:
    """An instrument-scoped sync event carrying a closed bar update."""

    event_id: str
    instrument_id: str
    timeframe: str
    bar: ClosedBar
    received_at: datetime

    @classmethod
    def create(
        cls,
        *,
        instrument_id: str,
        timeframe: str,
        bar: ClosedBar,
        received_at: datetime | None = None,
    ) -> "TimeframeSyncEvent":
        """Build a sync event for the timeframe store."""

        return cls(
            event_id=new_internal_id("sync"),
            instrument_id=instrument_id,
            timeframe=timeframe,
            bar=bar,
            received_at=received_at or utc_now(),
        )


@dataclass(frozen=True, slots=True)
class TimeframeContext:
    """Read-only MTF context assembled from the canonical timeframe store."""

    context_id: str
    instrument_id: str
    entry_timeframe: str
    timeframe_set: tuple[str, ...]
    bars: Mapping[str, ClosedBar]
    readiness_flags: Mapping[str, bool]
    freshness_flags: Mapping[str, bool]
    alignment_policy: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        instrument_id: str,
        entry_timeframe: str,
        timeframe_set: tuple[str, ...],
        bars: Mapping[str, ClosedBar],
        readiness_flags: Mapping[str, bool],
        freshness_flags: Mapping[str, bool],
        alignment_policy: str,
    ) -> "TimeframeContext":
        """Build a formal timeframe context for Wave 2A."""

        return cls(
            context_id=new_internal_id("ctx2"),
            instrument_id=instrument_id,
            entry_timeframe=entry_timeframe,
            timeframe_set=timeframe_set,
            bars=dict(bars),
            readiness_flags=dict(readiness_flags),
            freshness_flags=dict(freshness_flags),
            alignment_policy=alignment_policy,
            created_at=utc_now(),
        )

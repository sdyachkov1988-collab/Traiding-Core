"""Phase-scoped market context for the early MTF seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, utc_now
from trading_core.domain.events import MarketEvent


@dataclass(frozen=True, slots=True)
class MarketContext:
    """Early strategy-facing context without claiming full TimeframeContext maturity."""

    context_id: str
    instrument: InstrumentRef
    entry_timeframe: str
    timeframe_set: tuple[str, ...]
    latest_event: MarketEvent
    readiness_flags: Mapping[str, bool]
    alignment_policy: str
    created_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        instrument: InstrumentRef,
        entry_timeframe: str,
        timeframe_set: tuple[str, ...],
        latest_event: MarketEvent,
        readiness_flags: Mapping[str, bool],
        alignment_policy: str,
        metadata: Mapping[str, str] | None = None,
    ) -> "MarketContext":
        """Build the minimal phase-scoped context object for Package A."""

        return cls(
            context_id=new_internal_id("ctx"),
            instrument=instrument,
            entry_timeframe=entry_timeframe,
            timeframe_set=timeframe_set,
            latest_event=latest_event,
            readiness_flags=dict(readiness_flags),
            alignment_policy=alignment_policy,
            created_at=utc_now(),
            metadata=dict(metadata or {}),
        )

"""Phase-scoped market contexts for early seams."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, require_utc_datetime, utc_now
from trading_core.domain.timeframe import ClosedBar


@dataclass(frozen=True, slots=True)
class Wave1MtfContext:
    """Phase-scoped Wave 1 MTF input without claiming full TimeframeContext maturity."""

    context_id: str
    instrument: InstrumentRef
    entry_timeframe: str
    trend_timeframe: str
    entry_bar: ClosedBar | None
    trend_bar: ClosedBar | None
    closed_bar_only: bool
    no_lookahead_safe: bool
    readiness_flags: Mapping[str, bool]
    created_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.created_at, "created_at")

    @classmethod
    def create(
        cls,
        *,
        instrument: InstrumentRef,
        entry_timeframe: str,
        trend_timeframe: str,
        entry_bar: ClosedBar | None,
        trend_bar: ClosedBar | None,
        closed_bar_only: bool,
        no_lookahead_safe: bool,
        readiness_flags: Mapping[str, bool],
        metadata: Mapping[str, str] | None = None,
    ) -> "Wave1MtfContext":
        """Build a minimal Wave 1 MTF input object for the active contour."""

        return cls(
            context_id=new_internal_id("ctx1mtf"),
            instrument=instrument,
            entry_timeframe=entry_timeframe,
            trend_timeframe=trend_timeframe,
            entry_bar=entry_bar,
            trend_bar=trend_bar,
            closed_bar_only=closed_bar_only,
            no_lookahead_safe=no_lookahead_safe,
            readiness_flags=dict(readiness_flags),
            created_at=utc_now(),
            metadata=dict(metadata or {}),
        )

    @property
    def instrument_id(self) -> str:
        """Expose instrument_id without severing the full instrument lineage."""

        return self.instrument.instrument_id

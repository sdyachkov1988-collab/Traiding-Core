"""Concrete early context assembly for Package A."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.context.policies import parent_period_start, timeframe_to_seconds
from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain.common import InstrumentRef
from trading_core.domain.context import MarketContext, Wave1MtfContext
from trading_core.domain.events import MarketEvent


@dataclass(slots=True)
class SimpleMarketContextAssembler:
    """Build the phase-scoped market context from normalized events."""

    entry_timeframe: str = "15m"
    timeframe_set: tuple[str, ...] = ("15m",)
    alignment_policy: str = "closed-bars-only"

    def assemble(self, event: MarketEvent) -> MarketContext:
        """Return a minimal strategy-facing context for the next seam."""

        readiness_flags = {
            "event_received": True,
            "entry_ready": event.event_kind == "bar",
            "context_ready": True,
        }
        return MarketContext.create(
            instrument=event.instrument,
            entry_timeframe=self.entry_timeframe,
            timeframe_set=self.timeframe_set,
            latest_event=event,
            readiness_flags=readiness_flags,
            alignment_policy=self.alignment_policy,
            metadata={"source_event_id": event.event_id},
        )


@dataclass(slots=True)
class Wave1MtfContextAssembler:
    """Assemble a minimal Wave 1 MTF input object from canonical stored bars."""

    instrument: InstrumentRef
    store: InstrumentTimeframeStore
    entry_timeframe: str = "15m"
    trend_timeframe: str = "1h"

    def assemble(self) -> Wave1MtfContext:
        """Return the phase-scoped MTF input used by the active Wave 1 path."""

        entry_bar = self.store.get_bar(self.entry_timeframe)
        trend_bar = self.store.get_bar(self.trend_timeframe)
        readiness_flags = {
            "entry_ready": entry_bar is not None,
            "trend_ready": trend_bar is not None,
            "context_ready": entry_bar is not None and trend_bar is not None,
        }
        closed_bar_only = all(
            bar is not None and bar.is_closed is True
            for bar in (entry_bar, trend_bar)
        )
        no_lookahead_safe = False
        if entry_bar is not None and trend_bar is not None:
            entry_seconds = timeframe_to_seconds(self.entry_timeframe)
            trend_seconds = timeframe_to_seconds(self.trend_timeframe)
            if trend_seconds >= entry_seconds and trend_seconds % entry_seconds == 0:
                no_lookahead_safe = (
                    trend_bar.bar_time
                    == parent_period_start(entry_bar.bar_time, self.trend_timeframe)
                )
        return Wave1MtfContext.create(
            instrument_id=self.instrument.instrument_id,
            entry_timeframe=self.entry_timeframe,
            trend_timeframe=self.trend_timeframe,
            entry_bar=entry_bar,
            trend_bar=trend_bar,
            closed_bar_only=closed_bar_only,
            no_lookahead_safe=no_lookahead_safe,
            readiness_flags=readiness_flags,
            metadata={"instrument_symbol": self.instrument.symbol},
        )

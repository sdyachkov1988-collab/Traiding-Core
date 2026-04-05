"""Concrete early context assembly for Package A."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.domain.context import MarketContext
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

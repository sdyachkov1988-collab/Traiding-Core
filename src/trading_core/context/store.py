"""Instrument-scoped canonical timeframe store for Wave 2A."""

from __future__ import annotations

from typing import Mapping

from trading_core.domain.timeframe import ClosedBar, TimeframeSyncEvent


class InstrumentTimeframeStore:
    """Store the latest closed bar per timeframe for a single instrument."""

    def __init__(self, instrument_id: str) -> None:
        self.instrument_id = instrument_id
        self._bars: dict[str, ClosedBar] = {}

    def update(self, event: TimeframeSyncEvent) -> None:
        """Update the stored closed bar for the event timeframe."""

        if event.instrument_id != self.instrument_id:
            raise ValueError("TimeframeSyncEvent instrument_id does not match store")
        self._bars[event.timeframe] = event.bar

    def get_bars(self) -> Mapping[str, ClosedBar]:
        """Return the current timeframe-bar mapping."""

        return dict(self._bars)

    def get_bar(self, timeframe: str) -> ClosedBar | None:
        """Return the latest closed bar for a timeframe, if present."""

        return self._bars.get(timeframe)

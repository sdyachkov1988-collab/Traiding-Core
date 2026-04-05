"""Instrument-scoped canonical timeframe store for Wave 2A."""

from __future__ import annotations

from typing import Mapping

from trading_core.domain.timeframe import ClosedBar, TimeframeSyncEvent


class InstrumentTimeframeStore:
    """Store the latest closed bar per timeframe for a single instrument."""

    def __init__(self, instrument_id: str) -> None:
        self.instrument_id = instrument_id
        self._bars: dict[str, ClosedBar] = {}
        self._history_depths: dict[str, int] = {}

    def update(self, event: TimeframeSyncEvent) -> None:
        """Update the stored closed bar for the event timeframe."""

        if event.instrument_id != self.instrument_id:
            raise ValueError("TimeframeSyncEvent instrument_id does not match store")
        existing_bar = self._bars.get(event.timeframe)
        if existing_bar is not None and event.bar.bar_time < existing_bar.bar_time:
            raise ValueError("timeframe_bar_time_must_be_monotonic")

        self._bars[event.timeframe] = event.bar
        if existing_bar is None:
            self._history_depths[event.timeframe] = 1
        elif event.bar.bar_time > existing_bar.bar_time:
            self._history_depths[event.timeframe] = (
                self._history_depths.get(event.timeframe, 1) + 1
            )
        else:
            self._history_depths.setdefault(event.timeframe, 1)

    def get_bars(self) -> Mapping[str, ClosedBar]:
        """Return the current timeframe-bar mapping."""

        return dict(self._bars)

    def get_history_depth(self, timeframe: str) -> int:
        """Return how many monotonic bar updates were accepted for a timeframe."""

        return self._history_depths.get(timeframe, 0)

    def get_history_depths(self) -> Mapping[str, int]:
        """Return accepted history depth per timeframe."""

        return dict(self._history_depths)

    def get_bar(self, timeframe: str) -> ClosedBar | None:
        """Return the latest closed bar for a timeframe, if present."""

        return self._bars.get(timeframe)

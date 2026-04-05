"""Policies for the Wave 2A MTF foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from trading_core.domain.timeframe import ClosedBar


@dataclass(frozen=True, slots=True)
class BarAlignmentPolicy:
    """Define which timeframes must be present for a valid context."""

    entry_timeframe: str
    required_timeframes: tuple[str, ...]
    policy_name: str = "bar_alignment_policy"

    def is_aligned(self, bars: Mapping[str, ClosedBar]) -> bool:
        """Return True when required bars exist and higher-timeframe parents align."""

        if not all(timeframe in bars for timeframe in self.required_timeframes):
            return False

        entry_bar = bars[self.entry_timeframe]
        entry_seconds = self._timeframe_to_seconds(self.entry_timeframe)
        entry_timestamp = int(entry_bar.bar_time.timestamp())
        for timeframe in self.required_timeframes:
            if timeframe == self.entry_timeframe:
                continue

            higher_bar = bars[timeframe]
            higher_seconds = self._timeframe_to_seconds(timeframe)
            if higher_seconds < entry_seconds or higher_seconds % entry_seconds != 0:
                return False

            parent_period_start = (entry_timestamp // higher_seconds) * higher_seconds
            if int(higher_bar.bar_time.timestamp()) != parent_period_start:
                return False

        return True

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert a compact timeframe string like 15m or 1h into seconds."""

        if timeframe.endswith("m"):
            return int(timeframe[:-1]) * 60
        if timeframe.endswith("h"):
            return int(timeframe[:-1]) * 3600
        raise ValueError(f"unsupported timeframe format: {timeframe}")


@dataclass(frozen=True, slots=True)
class ClosedBarPolicy:
    """Validate that only closed bars enter the timeframe context."""

    def is_valid_closed_bar(self, bar: ClosedBar) -> bool:
        """Return True for bars that are formally marked as closed."""

        return bar.is_closed is True


@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    """Define how old a bar may be before it is considered stale."""

    max_age_seconds: int

    def is_fresh(self, bar: ClosedBar, now: datetime) -> bool:
        """Return True when the bar age stays within the configured limit."""

        return (now - bar.bar_time).total_seconds() <= self.max_age_seconds

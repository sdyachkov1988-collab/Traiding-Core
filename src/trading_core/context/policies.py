"""Policies for the Wave 2A MTF foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping

from trading_core.domain.timeframe import ClosedBar


def timeframe_to_seconds(timeframe: str) -> int:
    """Convert compact timeframe strings like 15m, 1h, 1d, 1w into seconds."""

    value = int(timeframe[:-1])
    unit = timeframe[-1]
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400
    if unit == "w":
        return value * 604800
    raise ValueError(f"unsupported timeframe format: {timeframe}")


def timeframe_duration(timeframe: str) -> timedelta:
    """Return the duration represented by a compact timeframe string."""

    return timedelta(seconds=timeframe_to_seconds(timeframe))


def parent_period_start(entry_bar_time: datetime, parent_timeframe: str) -> datetime:
    """Return the expected parent-period start for an entry bar time in UTC."""

    seconds = timeframe_to_seconds(parent_timeframe)
    if parent_timeframe.endswith("w"):
        start_of_day = entry_bar_time.astimezone(timezone.utc).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return start_of_day - timedelta(days=start_of_day.weekday())

    timestamp = int(entry_bar_time.timestamp())
    return datetime.fromtimestamp((timestamp // seconds) * seconds, tz=timezone.utc)


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
        entry_seconds = timeframe_to_seconds(self.entry_timeframe)
        for timeframe in self.required_timeframes:
            if timeframe == self.entry_timeframe:
                continue

            higher_bar = bars[timeframe]
            higher_seconds = timeframe_to_seconds(timeframe)
            if higher_seconds < entry_seconds or higher_seconds % entry_seconds != 0:
                return False

            expected_parent_start = parent_period_start(entry_bar.bar_time, timeframe)
            if higher_bar.bar_time != expected_parent_start:
                return False

        return True


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

        bar_close_time = bar.bar_time + timeframe_duration(bar.timeframe)
        return (now - bar_close_time).total_seconds() <= self.max_age_seconds

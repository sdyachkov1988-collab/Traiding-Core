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
        """Return True when all required timeframes are present."""

        return all(timeframe in bars for timeframe in self.required_timeframes)


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

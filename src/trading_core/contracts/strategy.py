"""Contracts for Package B seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.timeframe import TimeframeContext
from trading_core.domain.strategy import NoAction, StrategyIntent

StrategyResult = StrategyIntent | NoAction


class Strategy(Protocol):
    """Produce a strategy result for the currently exported timeframe-based seam."""

    def evaluate(self, context: TimeframeContext) -> StrategyResult:
        """Return either a strategy intent or explicit no-action for this seam."""

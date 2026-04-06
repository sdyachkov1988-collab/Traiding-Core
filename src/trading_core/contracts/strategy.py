"""Contracts for Package B seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.context import StrategyContext
from trading_core.domain.strategy import NoAction, StrategyIntent

StrategyResult = StrategyIntent | NoAction


class Strategy(Protocol):
    """Produce a formal strategy-side result from a valid context."""

    def evaluate(self, context: StrategyContext) -> StrategyResult:
        """Return either a strategy intent or explicit no-action."""

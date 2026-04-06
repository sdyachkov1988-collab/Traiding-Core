"""Contracts for Package B seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.context import Wave1MtfContext
from trading_core.domain.strategy import NoAction, StrategyIntent

StrategyResult = StrategyIntent | NoAction


class Strategy(Protocol):
    """Produce a formal strategy-side result from the active Wave 1 MTF context."""

    def evaluate(self, context: Wave1MtfContext) -> StrategyResult:
        """Return either a strategy intent or explicit no-action."""

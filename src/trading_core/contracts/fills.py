"""Contracts for Package F fill-driven spine."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.fills import Fill
from trading_core.domain.portfolio_state import PortfolioState, Position


class FillProcessor(Protocol):
    """Accept execution facts as fill inputs for the internal truth chain."""

    def accept(self, fill: Fill) -> Fill:
        """Return the accepted fill fact for downstream processing."""


class PositionEngine(Protocol):
    """Update position truth only from fill facts."""

    def apply(self, current: Position | None, fill: Fill) -> Position:
        """Return the next position state after the fill."""


class PortfolioEngine(Protocol):
    """Update portfolio truth only from fill facts and position truth."""

    def apply(self, current: PortfolioState, fill: Fill, position: Position) -> PortfolioState:
        """Return the next portfolio state after the fill."""

"""Contracts for the Wave 2B Context Gate seam."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.gate import GateOutcome
from trading_core.domain.timeframe import TimeframeContext


class ContextGateProtocol(Protocol):
    """Return a formal gate decision for the current timeframe context."""

    def check(self, context: TimeframeContext | None) -> GateOutcome:
        """Return a formal gate decision for the current context."""

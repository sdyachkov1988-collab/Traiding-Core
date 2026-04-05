"""Contracts for the Wave 2A timeframe context seam."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.timeframe import TimeframeContext


class TimeframeContextProvider(Protocol):
    """Provide a valid timeframe context or report that it is not ready."""

    def assemble(self) -> TimeframeContext | None:
        """Return a valid TimeframeContext or None if not ready."""

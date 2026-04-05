"""Contracts for Package A seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.context import MarketContext
from trading_core.domain.events import MarketEvent


class EventNormalizer(Protocol):
    """Convert upstream payloads into normalized domain events."""

    def normalize(self, raw_event: object) -> MarketEvent:
        """Return a normalized market event without strategy interpretation."""


class MarketContextAssembler(Protocol):
    """Build the early strategy-facing context from normalized events."""

    def assemble(self, event: MarketEvent) -> MarketContext:
        """Return the phase-scoped market context for Package A."""

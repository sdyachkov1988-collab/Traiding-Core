"""Contracts for Package A seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.context import Wave1MtfContext
from trading_core.domain.events import MarketEvent


class EventNormalizer(Protocol):
    """Convert upstream payloads into normalized domain events."""

    def normalize(self, raw_event: object) -> MarketEvent:
        """Return a normalized market event without strategy interpretation."""


class Wave1MtfContextAssembler(Protocol):
    """Build the phase-scoped Wave 1 MTF context from normalized events."""

    def assemble(self, event: MarketEvent) -> Wave1MtfContext:
        """Return the phase-scoped Wave 1 MTF context for Package A."""

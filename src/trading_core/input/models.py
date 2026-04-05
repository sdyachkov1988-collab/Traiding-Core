"""Input-layer helper models for Package A."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RawMarketEvent:
    """Minimal raw event shape accepted by the default normalizer."""

    instrument_id: str
    symbol: str
    venue: str
    event_kind: str
    source: str
    payload: Mapping[str, str]
    source_event_time: datetime | None = None
    market_type: str = "spot"
    metadata: Mapping[str, str] = field(default_factory=dict)


"""Domain primitives for normalized market events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, utc_now


class EventKind(StrEnum):
    """Minimal event kinds suitable for the first normalized input seam."""

    TRADE = "trade"
    QUOTE = "quote"
    BAR = "bar"
    BOOK = "book"


@dataclass(frozen=True, slots=True)
class MarketEvent:
    """Normalized market event accepted by the input seam.

    Expected payload schema by `EventKind`:

    - `BAR`: `{"open": str, "high": str, "low": str, "close": str, "volume": str, "timeframe": str}`
    - `TRADE`: `{"price": str, "quantity": str}`
    - `QUOTE`: `{"bid": str, "ask": str, "bid_size": str, "ask_size": str}`
    - `BOOK`: `{"bids": str, "asks": str}` where the values contain a serialized representation

    Values are represented as strings carrying Decimal-compatible numbers.
    Fields may be absent when the upstream source does not provide them.
    """

    event_id: str
    instrument: InstrumentRef
    event_kind: EventKind
    event_time: datetime
    observed_at: datetime
    payload: Mapping[str, str]
    source: str
    lineage_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        instrument: InstrumentRef,
        event_kind: EventKind,
        payload: Mapping[str, str],
        source: str,
        event_time: datetime | None = None,
        observed_at: datetime | None = None,
        lineage_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "MarketEvent":
        """Build a normalized event with generated identity."""

        return cls(
            event_id=new_internal_id("evt"),
            instrument=instrument,
            event_kind=event_kind,
            event_time=event_time or utc_now(),
            observed_at=observed_at or utc_now(),
            payload=dict(payload),
            source=source,
            lineage_id=lineage_id,
            metadata=dict(metadata or {}),
        )

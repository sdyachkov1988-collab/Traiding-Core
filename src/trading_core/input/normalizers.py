"""Concrete event normalizers for Package A."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from trading_core.domain.common import InstrumentRef
from trading_core.domain.events import EventKind, MarketEvent
from trading_core.input.models import RawMarketEvent


class DictEventNormalizer:
    """Normalize a dict-like raw payload into a domain MarketEvent."""

    def normalize(self, raw_event: object) -> MarketEvent:
        """Return a normalized event without adding strategy meaning."""

        parsed = self._coerce_raw_event(raw_event)
        instrument = InstrumentRef(
            instrument_id=parsed.instrument_id,
            symbol=parsed.symbol,
            venue=parsed.venue,
            market_type=parsed.market_type,
        )
        event_kind = EventKind(parsed.event_kind)
        return MarketEvent.create(
            instrument=instrument,
            event_kind=event_kind,
            payload=parsed.payload,
            source=parsed.source,
            metadata=parsed.metadata,
        )

    def _coerce_raw_event(self, raw_event: object) -> RawMarketEvent:
        """Accept either an explicit raw model or a dict-like source object."""

        if isinstance(raw_event, RawMarketEvent):
            return raw_event
        if not isinstance(raw_event, Mapping):
            raise TypeError("raw_event must be a RawMarketEvent or mapping")

        required_keys = {
            "instrument_id",
            "symbol",
            "venue",
            "event_kind",
            "source",
            "payload",
        }
        missing_keys = sorted(required_keys - set(raw_event))
        if missing_keys:
            missing = ", ".join(missing_keys)
            raise ValueError(f"raw_event is missing required keys: {missing}")

        payload = raw_event["payload"]
        if not isinstance(payload, Mapping):
            raise TypeError("raw_event['payload'] must be a mapping")

        metadata = raw_event.get("metadata", {})
        if not isinstance(metadata, Mapping):
            raise TypeError("raw_event['metadata'] must be a mapping")

        return RawMarketEvent(
            instrument_id=str(raw_event["instrument_id"]),
            symbol=str(raw_event["symbol"]),
            venue=str(raw_event["venue"]),
            event_kind=str(raw_event["event_kind"]),
            source=str(raw_event["source"]),
            payload={str(key): str(value) for key, value in payload.items()},
            market_type=str(raw_event.get("market_type", "spot")),
            metadata={str(key): str(value) for key, value in metadata.items()},
        )


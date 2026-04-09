from __future__ import annotations

from decimal import Decimal
from datetime import timezone

import pytest

from trading_core.context import InstrumentTimeframeStore
from trading_core.domain import ClosedBar, EventKind, TimeframeSyncEvent
from trading_core.domain.common import InstrumentRef
from trading_core.domain.common import utc_now
from trading_core.input import DictEventNormalizer, RawMarketEvent, Wave1MtfContextAssembler


def test_dict_event_normalizer_converts_mapping_into_market_event() -> None:
    normalizer = DictEventNormalizer()

    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {"timeframe": "15m", "close": "65000"},
            "metadata": {"feed": "paper"},
        }
    )

    assert event.instrument.instrument_id == "btc-usdt"
    assert event.event_kind == EventKind.BAR
    assert event.payload["close"] == "65000"
    assert event.metadata["feed"] == "paper"


def test_dict_event_normalizer_accepts_explicit_raw_model() -> None:
    normalizer = DictEventNormalizer()
    source_event_time = utc_now()

    event = normalizer.normalize(
        RawMarketEvent(
            instrument_id="eth-usdt",
            symbol="ETHUSDT",
            venue="binance",
            event_kind="trade",
            source="test-feed",
            payload={"price": "3200", "quantity": "0.5"},
            source_event_time=source_event_time,
        )
    )

    assert event.instrument.symbol == "ETHUSDT"
    assert event.event_kind == EventKind.TRADE
    assert event.event_time == source_event_time


def test_dict_event_normalizer_uses_source_event_time_when_provided() -> None:
    normalizer = DictEventNormalizer()
    source_event_time = utc_now()

    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {"timeframe": "15m", "close": "65000"},
            "source_event_time": source_event_time,
        }
    )

    assert event.event_time == source_event_time
    assert event.event_time.tzinfo == timezone.utc


def test_dict_event_normalizer_rejects_missing_required_keys() -> None:
    normalizer = DictEventNormalizer()

    with pytest.raises(ValueError):
        normalizer.normalize(
            {
                "instrument_id": "btc-usdt",
                "symbol": "BTCUSDT",
                "venue": "binance",
                "source": "test-feed",
                "payload": {"close": "65000"},
            }
        )


def test_wave1_mtf_context_assembler_builds_context_from_normalized_bar_event() -> None:
    normalizer = DictEventNormalizer()
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    store = InstrumentTimeframeStore("btc-usdt")
    trend_bar_time = utc_now().replace(minute=0, second=0, microsecond=0)
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=ClosedBar(
                timeframe="1h",
                open=Decimal("100"),
                high=Decimal("110"),
                low=Decimal("95"),
                close=Decimal("108"),
                volume=Decimal("12"),
                bar_time=trend_bar_time,
                is_closed=True,
            ),
        )
    )
    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {
                "timeframe": "15m",
                "open": "105",
                "high": "109",
                "low": "104",
                "close": "108",
                "volume": "5",
            },
            "source_event_time": trend_bar_time.replace(minute=15),
        }
    )

    context = Wave1MtfContextAssembler(
        instrument=instrument,
        store=store,
        entry_timeframe="15m",
        trend_timeframe="1h",
    ).assemble(event)

    assert context.instrument == instrument
    assert context.entry_bar is not None
    assert context.entry_bar.timeframe == "15m"
    assert context.readiness_flags["event_received"] is True
    assert context.metadata["source_event_id"] == event.event_id


def test_wave1_mtf_context_assembler_rejects_mismatched_instrument_linkage() -> None:
    normalizer = DictEventNormalizer()
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    event = normalizer.normalize(
        {
            "instrument_id": "eth-usdt",
            "symbol": "ETHUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {
                "timeframe": "15m",
                "open": "100",
                "high": "101",
                "low": "99",
                "close": "100.5",
                "volume": "1",
            },
        }
    )

    with pytest.raises(ValueError, match="event_instrument_and_assembler_must_match"):
        Wave1MtfContextAssembler(
            instrument=instrument,
            store=InstrumentTimeframeStore("btc-usdt"),
        ).assemble(event)

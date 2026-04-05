from __future__ import annotations

from datetime import timezone

import pytest

from trading_core.domain import EventKind
from trading_core.domain.common import utc_now
from trading_core.input import DictEventNormalizer, RawMarketEvent, SimpleMarketContextAssembler


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


def test_simple_market_context_assembler_builds_phase_scoped_context() -> None:
    normalizer = DictEventNormalizer()
    assembler = SimpleMarketContextAssembler(
        entry_timeframe="15m",
        timeframe_set=("15m", "1h"),
        alignment_policy="closed-bars-only",
    )

    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {"timeframe": "15m", "close": "65000"},
        }
    )
    context = assembler.assemble(event)

    assert context.instrument.symbol == "BTCUSDT"
    assert context.entry_timeframe == "15m"
    assert context.timeframe_set == ("15m", "1h")
    assert context.readiness_flags["entry_ready"] is True
    assert context.metadata["source_event_id"] == event.event_id

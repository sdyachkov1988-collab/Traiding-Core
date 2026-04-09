from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from trading_core.context import (
    BarAlignmentPolicy,
    ClosedBarPolicy,
    FreshnessPolicy,
    InstrumentTimeframeStore,
    TimeframeContextAssembler,
)
from trading_core.domain import ClosedBar, TimeframeContext, TimeframeSyncEvent
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.domain import OrderSide
from trading_core.domain.strategy import NoAction, StrategyIntent
from trading_core.input import DictEventNormalizer, Wave1MtfContextAssembler
from trading_core.strategy import MtfBarAlignmentStrategy


def build_wave1_context(*, open_value: str, close_value: str):
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
                close=Decimal(close_value),
                volume=Decimal("12"),
                bar_time=trend_bar_time,
                is_closed=True,
            ),
        )
    )
    assembler = Wave1MtfContextAssembler(
        instrument=instrument,
        store=store,
        entry_timeframe="15m",
        trend_timeframe="1h",
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
                "open": open_value,
                "high": "106",
                "low": "95",
                "close": close_value,
                "volume": "10",
            },
        }
    )
    return assembler.assemble(event)


def test_mtf_bar_alignment_strategy_returns_buy_intent_for_green_aligned_bars() -> None:
    strategy = MtfBarAlignmentStrategy(min_entry_body_ratio=Decimal("0.001"))
    context = build_wave1_context(open_value="100", close_value="102")

    result = strategy.evaluate(context)

    assert isinstance(result, StrategyIntent)
    assert result.side == OrderSide.BUY
    assert result.strategy_name == "mtf_bar_alignment"


def test_mtf_bar_alignment_strategy_returns_sell_intent_for_red_aligned_bars() -> None:
    strategy = MtfBarAlignmentStrategy(min_entry_body_ratio=Decimal("0.001"))
    context = build_wave1_context(open_value="100", close_value="98")

    result = strategy.evaluate(context)

    assert isinstance(result, StrategyIntent)
    assert result.side == OrderSide.SELL


def test_mtf_bar_alignment_strategy_returns_no_action_for_small_entry_bar_body() -> None:
    strategy = MtfBarAlignmentStrategy(min_entry_body_ratio=Decimal("0.01"))
    context = build_wave1_context(open_value="100", close_value="100.2")

    result = strategy.evaluate(context)

    assert isinstance(result, NoAction)
    assert result.reason == "entry_bar_body_too_small"


def test_mtf_bar_alignment_strategy_returns_no_action_when_context_not_ready() -> None:
    strategy = MtfBarAlignmentStrategy()
    context = build_wave1_context(open_value="100", close_value="102")
    object.__setattr__(
        context,
        "readiness_flags",
        {"event_received": True, "entry_ready": False, "trend_ready": True, "context_ready": False},
    )

    result = strategy.evaluate(context)

    assert isinstance(result, NoAction)
    assert result.reason == "context_not_ready"


def test_mtf_bar_alignment_strategy_uses_context_instrument_lineage() -> None:
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    store = InstrumentTimeframeStore("btc-usdt")
    trend_bar_time = utc_now().replace(minute=0, second=0, microsecond=0)
    entry_bar_time = trend_bar_time + timedelta(minutes=15)
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=ClosedBar(
                timeframe="1h",
                open=Decimal("100"),
                high=Decimal("110"),
                low=Decimal("99"),
                close=Decimal("107"),
                volume=Decimal("12"),
                bar_time=trend_bar_time,
                is_closed=True,
            ),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=ClosedBar(
                timeframe="15m",
                open=Decimal("105"),
                high=Decimal("109"),
                low=Decimal("104"),
                close=Decimal("108"),
                volume=Decimal("4"),
                bar_time=entry_bar_time,
                is_closed=True,
            ),
        )
    )
    context = TimeframeContextAssembler(
        instrument_id=instrument.instrument_id,
        store=store,
        instrument=instrument,
        alignment_policy=BarAlignmentPolicy(
            entry_timeframe="15m",
            required_timeframes=("15m", "1h"),
        ),
        closed_bar_policy=ClosedBarPolicy(),
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
    ).assemble()

    assert isinstance(context, TimeframeContext)

    result = MtfBarAlignmentStrategy().evaluate(context)

    assert isinstance(result, StrategyIntent)
    assert result.instrument == context.instrument
    assert result.instrument.instrument_id == "btc-usdt"

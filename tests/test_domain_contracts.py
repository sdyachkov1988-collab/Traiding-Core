from __future__ import annotations

from dataclasses import is_dataclass
from datetime import timezone
from decimal import Decimal

import pytest

from trading_core.domain import (
    EventKind,
    InstrumentRef,
    MarketEvent,
    OrderIntent,
    OrderSide,
    OrderType,
    RiskDecision,
    RiskVerdict,
    StrategyIntent,
    TimeInForce,
    Wave1MtfContext,
)


def test_market_event_create_produces_timezone_aware_values() -> None:
    instrument = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")
    event = MarketEvent.create(
        instrument=instrument,
        event_kind=EventKind.BAR,
        payload={"timeframe": "1m"},
        source="test-feed",
    )

    assert event.event_id.startswith("evt_")
    assert event.event_time.tzinfo == timezone.utc
    assert event.observed_at.tzinfo == timezone.utc


def test_wave1_mtf_context_create_keeps_phase_scoped_shape() -> None:
    instrument = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")
    context = Wave1MtfContext.create(
        instrument=instrument,
        entry_timeframe="15m",
        trend_timeframe="1h",
        entry_bar=None,
        trend_bar=None,
        closed_bar_only=True,
        no_lookahead_safe=True,
        readiness_flags={"entry_ready": True, "trend_ready": True, "context_ready": True},
    )

    assert context.context_id.startswith("ctx1mtf_")
    assert context.readiness_flags["entry_ready"] is True


def test_strategy_risk_order_chain_has_distinct_entities() -> None:
    instrument = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")
    intent = StrategyIntent.create(
        instrument=instrument,
        side=OrderSide.BUY,
        thesis="breakout",
        confidence=Decimal("0.75"),
        strategy_name="test_strategy",
        context_id="ctx_123",
    )
    decision = RiskDecision.create(
        verdict=RiskVerdict.APPROVED,
        strategy_intent_id=intent.intent_id,
        instrument=instrument,
        side=intent.side,
        approved_quantity=Decimal("0.010"),
    )
    order_intent = OrderIntent.create(
        risk_decision_id=decision.risk_decision_id,
        instrument=instrument,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.010"),
        limit_price=Decimal("65000"),
        time_in_force=TimeInForce.GTC,
    )

    assert intent.intent_id.startswith("intent_")
    assert decision.risk_decision_id.startswith("risk_")
    assert order_intent.order_intent_id.startswith("ordint_")
    assert decision.strategy_intent_id == intent.intent_id
    assert decision.instrument == instrument
    assert decision.side == intent.side
    assert order_intent.risk_decision_id == decision.risk_decision_id


def test_core_entities_are_dataclasses() -> None:
    assert is_dataclass(MarketEvent)
    assert is_dataclass(Wave1MtfContext)
    assert is_dataclass(StrategyIntent)
    assert is_dataclass(RiskDecision)
    assert is_dataclass(OrderIntent)


def test_strategy_intent_rejects_out_of_range_confidence() -> None:
    instrument = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")

    with pytest.raises(ValueError):
        StrategyIntent.create(
            instrument=instrument,
            side=OrderSide.BUY,
            thesis="test",
            confidence=Decimal("-0.1"),
            strategy_name="test",
            context_id="ctx_123",
        )

    with pytest.raises(ValueError):
        StrategyIntent.create(
            instrument=instrument,
            side=OrderSide.BUY,
            thesis="test",
            confidence=Decimal("1.1"),
            strategy_name="test",
            context_id="ctx_123",
        )


def test_order_intent_rejects_non_positive_quantity() -> None:
    instrument = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")

    with pytest.raises(ValueError, match="quantity_must_be_positive"):
        OrderIntent.create(
            risk_decision_id="risk_1",
            instrument=instrument,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0"),
            time_in_force=TimeInForce.IOC,
        )


def test_order_intent_rejects_market_limit_price_leak() -> None:
    instrument = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")

    with pytest.raises(ValueError, match="market_order_must_not_define_limit_price"):
        OrderIntent.create(
            risk_decision_id="risk_1",
            instrument=instrument,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.01"),
            limit_price=Decimal("100"),
            time_in_force=TimeInForce.IOC,
        )

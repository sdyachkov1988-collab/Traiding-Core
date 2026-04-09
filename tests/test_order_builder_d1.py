from __future__ import annotations

from decimal import Decimal

import pytest

from trading_core.domain import (
    CloseIntent,
    ExecutionConstraintBasis,
    InstrumentRef,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    OrderSide,
    OrderType,
    PortfolioRiskBasis,
    RiskVerdict,
    TimeInForce,
)
from trading_core.execution.builders import SimpleOrderIntentBuilder
from trading_core.input import DictEventNormalizer, Wave1MtfContextAssembler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.strategy import MtfBarAlignmentStrategy
from trading_core.context import InstrumentTimeframeStore
from trading_core.domain import ClosedBar, TimeframeSyncEvent
from trading_core.domain.common import utc_now


def build_approved_decision():
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
                high=Decimal("106"),
                low=Decimal("95"),
                close=Decimal("105"),
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
    strategy = MtfBarAlignmentStrategy(min_entry_body_ratio=Decimal("0.001"))
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {
                "timeframe": "15m",
                "open": "100",
                "high": "106",
                "low": "99",
                "close": "105",
                "volume": "10",
            },
        }
    )
    context = assembler.assemble(event)
    intent = strategy.evaluate(context)
    return risk.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("105.00"),
        ),
    )


def test_order_builder_builds_only_order_intent_from_approved_decision() -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()

    order_intent = builder.build(
        decision=decision,
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_order_quantity=Decimal("0.01"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
    )

    assert decision.verdict == RiskVerdict.APPROVED
    assert order_intent.order_type == OrderType.LIMIT
    assert order_intent.time_in_force == TimeInForce.GTC
    assert order_intent.limit_price == Decimal("105.20")
    assert order_intent.quantity == Decimal("0.11")


def test_order_builder_rejects_non_approved_decision() -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()
    rejected = type(decision).create(
        verdict=RiskVerdict.REJECTED,
        strategy_intent_id=decision.strategy_intent_id,
        instrument=decision.instrument,
        side=decision.side,
        rejection_reason="manual_rejection",
    )

    with pytest.raises(ValueError):
        builder.build(
            decision=rejected,
            instrument_spec=InstrumentExecutionSpec(
                instrument_id="btc-usdt",
                quantity_step=Decimal("0.01"),
                price_step=Decimal("0.10"),
                min_order_quantity=Decimal("0.01"),
                supported_order_types=(OrderType.LIMIT,),
                supported_time_in_force=(TimeInForce.GTC,),
            ),
            execution_basis=ExecutionConstraintBasis(reference_price=Decimal("105.00")),
        )


def test_order_builder_validates_instrument_match() -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()

    with pytest.raises(ValueError):
        builder.build(
            decision=decision,
            instrument_spec=InstrumentExecutionSpec(
                instrument_id="eth-usdt",
                quantity_step=Decimal("0.01"),
                price_step=Decimal("0.10"),
                min_order_quantity=Decimal("0.01"),
                supported_order_types=(OrderType.LIMIT,),
                supported_time_in_force=(TimeInForce.GTC,),
            ),
            execution_basis=ExecutionConstraintBasis(reference_price=Decimal("105.00")),
        )


def test_order_builder_accepts_capped_decision_and_builds_order_intent() -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()
    capped = type(decision).create(
        verdict=RiskVerdict.CAPPED,
        strategy_intent_id=decision.strategy_intent_id,
        instrument=decision.instrument,
        side=decision.side,
        approved_quantity=Decimal("0.05"),
        rejection_reason="clamped_to_max_order_quantity",
    )

    order_intent = builder.build(
        decision=capped,
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_order_quantity=Decimal("0.01"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
    )

    assert order_intent.quantity == Decimal("0.05")


def test_order_builder_rejects_quantity_that_falls_below_min_after_rounding() -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()
    rounded_below_min = type(decision).create(
        verdict=RiskVerdict.APPROVED,
        strategy_intent_id=decision.strategy_intent_id,
        instrument=decision.instrument,
        side=decision.side,
        approved_quantity=Decimal("0.019"),
    )

    with pytest.raises(ValueError, match="Rounded quantity fell below instrument minimum quantity"):
        builder.build(
            decision=rounded_below_min,
            instrument_spec=InstrumentExecutionSpec(
                instrument_id="btc-usdt",
                quantity_step=Decimal("0.01"),
                price_step=Decimal("0.10"),
                min_order_quantity=Decimal("0.015"),
                supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
                supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            ),
            execution_basis=ExecutionConstraintBasis(
                reference_price=Decimal("105.00"),
                preferred_limit_offset=Decimal("0.20"),
            ),
        )


def test_order_builder_rejects_non_positive_limit_price() -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()
    sell_decision = type(decision).create(
        verdict=RiskVerdict.APPROVED,
        strategy_intent_id=decision.strategy_intent_id,
        instrument=decision.instrument,
        side=OrderSide.SELL,
        approved_quantity=decision.approved_quantity,
    )

    with pytest.raises(ValueError, match="Limit price must be positive"):
        builder.build(
            decision=sell_decision,
            instrument_spec=InstrumentExecutionSpec(
                instrument_id="btc-usdt",
                quantity_step=Decimal("0.01"),
                price_step=Decimal("0.10"),
                min_order_quantity=Decimal("0.01"),
                supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
                supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            ),
            execution_basis=ExecutionConstraintBasis(
                reference_price=Decimal("0.05"),
                preferred_limit_offset=Decimal("0.10"),
            ),
        )


@pytest.mark.parametrize(
    ("approved_quantity", "quantity_step", "expected_quantity"),
    [
        (Decimal("0.29"), Decimal("0.05"), Decimal("0.25")),
        (Decimal("0.49"), Decimal("0.25"), Decimal("0.25")),
    ],
)
def test_order_builder_aligns_quantity_by_true_step_multiple(
    approved_quantity: Decimal,
    quantity_step: Decimal,
    expected_quantity: Decimal,
) -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()
    aligned = type(decision).create(
        verdict=RiskVerdict.APPROVED,
        strategy_intent_id=decision.strategy_intent_id,
        instrument=decision.instrument,
        side=decision.side,
        approved_quantity=approved_quantity,
    )

    order_intent = builder.build(
        decision=aligned,
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=quantity_step,
            price_step=Decimal("0.10"),
            min_order_quantity=Decimal("0.01"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
    )

    assert order_intent.quantity == expected_quantity


@pytest.mark.parametrize(
    ("price_step", "expected_price"),
    [
        (Decimal("0.05"), Decimal("105.20")),
        (Decimal("0.125"), Decimal("105.125")),
    ],
)
def test_order_builder_aligns_limit_price_by_true_step_multiple(
    price_step: Decimal,
    expected_price: Decimal,
) -> None:
    decision = build_approved_decision()
    builder = SimpleOrderIntentBuilder()

    order_intent = builder.build(
        decision=decision,
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=price_step,
            min_order_quantity=Decimal("0.01"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
    )

    assert order_intent.limit_price == expected_price


def test_close_order_builder_validates_instrument_match() -> None:
    builder = SimpleOrderIntentBuilder()
    close_intent = CloseIntent.create(
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        position_id="pos_1",
        quantity=Decimal("0.25"),
        reason="protective_close",
    )

    with pytest.raises(ValueError, match="Instrument spec does not match CloseIntent instrument"):
        builder.build_close_order(
            close_intent=close_intent,
            instrument_spec=InstrumentExecutionSpec(
                instrument_id="eth-usdt",
                quantity_step=Decimal("0.05"),
                price_step=Decimal("0.125"),
                min_order_quantity=Decimal("0.05"),
                supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
                supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            ),
            execution_basis=ExecutionConstraintBasis(
                reference_price=Decimal("105.00"),
                preferred_limit_offset=Decimal("0.20"),
            ),
        )

from __future__ import annotations

from decimal import Decimal

import pytest

from trading_core.domain import (
    ExecutionConstraintBasis,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    OrderSide,
    OrderType,
    PortfolioRiskBasis,
    RiskVerdict,
    TimeInForce,
)
from trading_core.execution.builders import SimpleOrderIntentBuilder
from trading_core.input import DictEventNormalizer, SimpleMarketContextAssembler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.strategy import BarDirectionStrategy


def build_approved_decision():
    normalizer = DictEventNormalizer()
    assembler = SimpleMarketContextAssembler(
        entry_timeframe="15m",
        timeframe_set=("15m", "1h"),
        alignment_policy="closed-bars-only",
    )
    strategy = BarDirectionStrategy(min_body_ratio=Decimal("0.001"))
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {"timeframe": "15m", "open": "100", "close": "105"},
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

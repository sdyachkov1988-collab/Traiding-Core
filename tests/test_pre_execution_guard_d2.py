from __future__ import annotations

from decimal import Decimal

import pytest

from trading_core.domain import (
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    GuardVerdict,
    InstrumentExecutionSpec,
    InstrumentRef,
    InstrumentRiskBasis,
    OrderType,
    PortfolioRiskBasis,
    TimeInForce,
)
from trading_core.execution import SimpleOrderIntentBuilder, SimplePreExecutionGuard
from trading_core.input import DictEventNormalizer, Wave1MtfContextAssembler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.strategy import MtfBarAlignmentStrategy
from trading_core.context import InstrumentTimeframeStore
from trading_core.domain import ClosedBar, TimeframeSyncEvent
from trading_core.domain.common import utc_now


def build_order_intent():
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
    builder = SimpleOrderIntentBuilder()

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
    decision = risk.evaluate(
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
    return builder.build(
        decision=decision,
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
    )


def test_pre_execution_guard_passes_valid_order_intent() -> None:
    order_intent = build_order_intent()
    guard = SimplePreExecutionGuard()

    outcome = guard.check(
        intent=order_intent,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("10"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            reference_price=Decimal("105.00"),
        ),
    )

    assert outcome.verdict == GuardVerdict.PASSED
    assert outcome.reason is None


def test_pre_execution_guard_rejects_below_min_qty() -> None:
    order_intent = build_order_intent()
    guard = SimplePreExecutionGuard()
    too_small = type(order_intent).create(
        risk_decision_id=order_intent.risk_decision_id,
        instrument=order_intent.instrument,
        side=order_intent.side,
        order_type=order_intent.order_type,
        quantity=Decimal("0.001"),
        time_in_force=order_intent.time_in_force,
        limit_price=order_intent.limit_price,
        metadata=order_intent.metadata,
    )

    outcome = guard.check(
        intent=too_small,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.001"),
            price_step=Decimal("0.10"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("10"),
            supported_order_types=(OrderType.LIMIT,),
            supported_time_in_force=(TimeInForce.GTC,),
            reference_price=Decimal("105.00"),
        ),
    )

    assert outcome.verdict == GuardVerdict.REJECTED
    assert outcome.reason == "below_min_qty"


def test_pre_execution_guard_rejects_below_min_notional() -> None:
    order_intent = build_order_intent()
    guard = SimplePreExecutionGuard()

    outcome = guard.check(
        intent=order_intent,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("1000"),
            supported_order_types=(OrderType.LIMIT,),
            supported_time_in_force=(TimeInForce.GTC,),
            reference_price=Decimal("105.00"),
        ),
    )

    assert outcome.verdict == GuardVerdict.REJECTED
    assert outcome.reason == "below_min_notional"


def test_pre_execution_guard_rejects_unsupported_order_type() -> None:
    order_intent = build_order_intent()
    guard = SimplePreExecutionGuard()

    outcome = guard.check(
        intent=order_intent,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("10"),
            supported_order_types=(OrderType.MARKET,),
            supported_time_in_force=(TimeInForce.GTC,),
            reference_price=Decimal("105.00"),
        ),
    )

    assert outcome.verdict == GuardVerdict.REJECTED
    assert outcome.reason == "order_type_not_supported"


def test_pre_execution_guard_rejects_limit_price_not_aligned_to_price_step() -> None:
    order_intent = build_order_intent()
    guard = SimplePreExecutionGuard()
    misaligned_price = type(order_intent).create(
        risk_decision_id=order_intent.risk_decision_id,
        instrument=order_intent.instrument,
        side=order_intent.side,
        order_type=order_intent.order_type,
        quantity=order_intent.quantity,
        time_in_force=order_intent.time_in_force,
        limit_price=Decimal("105.23"),
        metadata=order_intent.metadata,
    )

    outcome = guard.check(
        intent=misaligned_price,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.05"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("10"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            reference_price=Decimal("105.00"),
        ),
    )

    assert outcome.verdict == GuardVerdict.REJECTED
    assert outcome.reason == "price_rounding_invalid"


def test_pre_execution_guard_rejects_non_positive_limit_price_with_explicit_reason() -> None:
    order_intent = build_order_intent()
    with pytest.raises(ValueError, match="limit_price_must_be_positive"):
        type(order_intent).create(
            risk_decision_id=order_intent.risk_decision_id,
            instrument=order_intent.instrument,
            side=order_intent.side,
            order_type=order_intent.order_type,
            quantity=order_intent.quantity,
            time_in_force=order_intent.time_in_force,
            limit_price=Decimal("0"),
            metadata=order_intent.metadata,
        )

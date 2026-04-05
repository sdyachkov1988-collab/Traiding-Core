from __future__ import annotations

from decimal import Decimal

from trading_core.domain import (
    AdmittedOrder,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReportKind,
    GuardVerdict,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    OrderType,
    PortfolioRiskBasis,
    TimeInForce,
)
from trading_core.execution import (
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.input import DictEventNormalizer, SimpleMarketContextAssembler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.strategy import BarDirectionStrategy


def build_admitted_order() -> AdmittedOrder:
    normalizer = DictEventNormalizer()
    assembler = SimpleMarketContextAssembler(
        entry_timeframe="15m",
        timeframe_set=("15m", "1h"),
        alignment_policy="closed-bars-only",
    )
    strategy = BarDirectionStrategy(min_body_ratio=Decimal("0.001"))
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    builder = SimpleOrderIntentBuilder()
    guard = SimplePreExecutionGuard()

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
    decision = risk.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("5.00"),
            max_capital_per_trade=Decimal("2.00"),
        ),
    )
    order_intent = builder.build(
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
    assert outcome.verdict is GuardVerdict.PASSED
    return AdmittedOrder.create(order_intent=order_intent, guard_outcome=outcome)


def test_mock_execution_adapter_returns_only_normalized_reports() -> None:
    adapter = MockExecutionAdapter(accept_orders=True)
    admitted_order = build_admitted_order()

    reports = adapter.submit(admitted_order)

    assert len(reports) == 3
    assert tuple(report.kind for report in reports) == (
        ExecutionReportKind.SUBMITTED,
        ExecutionReportKind.ACCEPTED,
        ExecutionReportKind.ACKNOWLEDGED,
    )
    assert all(
        report.order_intent_id == admitted_order.order_intent.order_intent_id
        for report in reports
    )


def test_mock_execution_adapter_can_return_rejected_report_sequence() -> None:
    adapter = MockExecutionAdapter(accept_orders=False)
    admitted_order = build_admitted_order()

    reports = adapter.submit(admitted_order)

    assert tuple(report.kind for report in reports) == (
        ExecutionReportKind.SUBMITTED,
        ExecutionReportKind.REJECTED,
    )
    assert reports[-1].reason == "adapter_rejected_submission"

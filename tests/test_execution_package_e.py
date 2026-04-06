from __future__ import annotations

from decimal import Decimal

from trading_core.domain import (
    AdmittedOrder,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReport,
    ExecutionReportKind,
    GuardOutcome,
    GuardVerdict,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    InstrumentRef,
    OrderIntent,
    OrderSide,
    OrderType,
    PortfolioRiskBasis,
    TimeInForce,
)
from trading_core.execution import (
    ExecutionHandoff,
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
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("105.00"),
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


def test_mock_execution_adapter_materializes_limit_fill_from_order_limit_price() -> None:
    adapter = MockExecutionAdapter(accept_orders=True)
    admitted_order = build_admitted_order()
    accepted_report = next(
        report for report in adapter.submit(admitted_order) if report.kind is ExecutionReportKind.ACCEPTED
    )

    fill = adapter.materialize_fill(admitted_order, accepted_report, fee=Decimal("0.25"))

    assert fill.price == admitted_order.order_intent.limit_price
    assert fill.external_fill_id != accepted_report.external_order_id
    assert fill.metadata["external_order_id"] == accepted_report.external_order_id
    assert fill.metadata["execution_price_source"] == "order_limit_price"
    assert fill.metadata["execution_report_id"] == accepted_report.report_id


def test_mock_execution_adapter_materializes_market_fill_from_explicit_execution_price() -> None:
    adapter = MockExecutionAdapter(accept_orders=True)
    market_order = OrderIntent.create(
        risk_decision_id="risk_1",
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.50"),
        time_in_force=TimeInForce.IOC,
        limit_price=None,
    )
    guard_outcome = GuardOutcome.create(
        order_intent_id=market_order.order_intent_id,
        verdict=GuardVerdict.PASSED,
        metadata={"checked_constraint": "market_order_allowed"},
    )
    admitted_order = AdmittedOrder.create(
        order_intent=market_order,
        guard_outcome=guard_outcome,
    )
    accepted_report = next(
        report for report in adapter.submit(admitted_order) if report.kind is ExecutionReportKind.ACCEPTED
    )

    fill = adapter.materialize_fill(
        admitted_order,
        accepted_report,
        execution_price=Decimal("104.75"),
    )

    assert fill.price == Decimal("104.75")
    assert fill.external_fill_id != accepted_report.external_order_id
    assert fill.metadata["external_order_id"] == accepted_report.external_order_id
    assert fill.metadata["execution_price_source"] == "explicit_execution_price"


def test_mock_execution_adapter_materialize_fill_rejects_invalid_report_kind() -> None:
    adapter = MockExecutionAdapter(accept_orders=True)
    admitted_order = build_admitted_order()
    submitted_report = next(
        report for report in adapter.submit(admitted_order) if report.kind is ExecutionReportKind.SUBMITTED
    )

    try:
        adapter.materialize_fill(admitted_order, submitted_report)
    except ValueError as exc:
        assert str(exc) == "Fill materialization requires an accepted or acknowledged report"
    else:
        raise AssertionError("Expected invalid report kind to be rejected")


def test_mock_execution_adapter_materialize_fill_rejects_mismatched_report() -> None:
    adapter = MockExecutionAdapter(accept_orders=True)
    admitted_order = build_admitted_order()
    mismatched_report = ExecutionReport.create(
        kind=ExecutionReportKind.ACCEPTED,
        order_intent_id="ordint_other",
        external_order_id="mock_ordint_other",
    )

    try:
        adapter.materialize_fill(admitted_order, mismatched_report)
    except ValueError as exc:
        assert str(exc) == "ExecutionReport does not match AdmittedOrder"
    else:
        raise AssertionError("Expected mismatched report to be rejected")


def test_execution_handoff_exposes_extended_execution_capabilities() -> None:
    instrument_spec = InstrumentExecutionSpec(
        instrument_id="btc-usdt",
        quantity_step=Decimal("0.01"),
        price_step=Decimal("0.10"),
        min_order_quantity=Decimal("0.01"),
        supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
        supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
    )
    adapter = MockExecutionAdapter(
        accept_orders=True,
        balances={"USDT": Decimal("1000.00")},
        instrument_specs={"btc-usdt": instrument_spec},
    )
    handoff = ExecutionHandoff(adapter=adapter)
    admitted_order = build_admitted_order()

    reports = handoff.place(admitted_order)
    accepted = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    queried_reports = handoff.query(accepted.external_order_id or "")
    cancelled_reports = handoff.cancel(accepted.external_order_id or "")

    assert handoff.get_balances()["USDT"] == Decimal("1000.00")
    assert handoff.get_instrument_spec("btc-usdt") == instrument_spec
    assert queried_reports == reports
    assert cancelled_reports[-1].kind is ExecutionReportKind.CANCELLED

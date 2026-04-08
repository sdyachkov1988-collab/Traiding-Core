from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain import (
    AdmittedOrder,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReport,
    ExecutionReportKind,
    ExternalStartupBasis,
    ExternalStartupOrderRecord,
    ExternalStartupPosition,
    Fill,
    GuardOutcome,
    GuardVerdict,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    OrderIntent,
    OrderSide,
    OrderType,
    PortfolioRiskBasis,
    PortfolioState,
    Position,
    RiskDecision,
    StartupReconciliationVerdict,
    StrategyIntent,
    TimeInForce,
    Wave1MtfContext,
)
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.domain.state import PersistedOrderRecord
from trading_core.execution import (
    ExecutionHandoff,
    IdempotentFillProcessor,
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.input import DictEventNormalizer, Wave1MtfContextAssembler
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import SpotPositionEngine
from trading_core.reconciliation import SimpleStartupReconciler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.state import JsonFileStateStore
from trading_core.strategy import MtfBarAlignmentStrategy


def build_wave1g_minimal_core_pipeline() -> tuple[
    InstrumentRef,
    Wave1MtfContext,
    StrategyIntent,
    RiskDecision,
    OrderIntent,
    GuardOutcome,
    AdmittedOrder,
]:
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    normalizer = DictEventNormalizer()
    assembler = Wave1MtfContextAssembler(
        instrument=instrument,
        store=InstrumentTimeframeStore(instrument.instrument_id),
        entry_timeframe="15m",
        trend_timeframe="1h",
    )
    strategy = MtfBarAlignmentStrategy()
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    builder = SimpleOrderIntentBuilder()
    guard = SimplePreExecutionGuard()

    now = utc_now().replace(second=0, microsecond=0)
    trend_bar_time = now.replace(minute=0) - timedelta(hours=1)
    entry_bar_time = trend_bar_time + timedelta(minutes=45)
    trend_event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "source_event_time": trend_bar_time,
            "payload": {
                "timeframe": "1h",
                "open": "95",
                "high": "106",
                "low": "94",
                "close": "104",
                "volume": "40",
            },
        }
    )
    entry_event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "source_event_time": entry_bar_time,
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
    assembler.assemble(trend_event)
    context = assembler.assemble(entry_event)
    strategy_intent = strategy.evaluate(context)
    assert isinstance(strategy_intent, StrategyIntent)

    risk_decision = risk.evaluate(
        intent=strategy_intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("500"),
            max_capital_per_trade=Decimal("250"),
            reference_price=Decimal("105.00"),
        ),
    )
    order_intent = builder.build(
        decision=risk_decision,
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
    guard_outcome = guard.check(
        intent=order_intent,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("1"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            reference_price=Decimal("105.00"),
        ),
    )
    admitted_order = AdmittedOrder.create(order_intent=order_intent, guard_outcome=guard_outcome)
    return (
        instrument,
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    )


def test_wave1g_minimal_core_happy_path_reaches_startup_reconciliation(tmp_path: Path) -> None:
    (
        _instrument,
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    ) = build_wave1g_minimal_core_pipeline()
    handoff = ExecutionHandoff(adapter=MockExecutionAdapter(accept_orders=True))
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    store = JsonFileStateStore(tmp_path / "state" / "latest.json")

    reports = handoff.place(admitted_order)
    accepted_report = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    fill = handoff.materialize_fill(admitted_order, accepted_report)
    accepted_fill = fill_processor.accept(fill)
    position = position_engine.apply(None, accepted_fill)
    portfolio = portfolio_engine.apply(
        PortfolioState.empty(cash_balance=Decimal("1000")),
        accepted_fill,
        position,
    )
    order_picture = {
        order_intent.order_intent_id: PersistedOrderRecord(
            order_intent_id=order_intent.order_intent_id,
            external_order_id=accepted_report.external_order_id,
            last_report_kind=accepted_report.kind,
            observed_at=accepted_report.observed_at,
            metadata={"boundary": "package_e"},
        )
    }
    snapshot = store.save_with_fill_marker(
        portfolio,
        fill.fill_id,
        order_picture=order_picture,
    )
    result = SimpleStartupReconciler().reconcile(
        snapshot,
        ExternalStartupBasis.create(
            cash_balance=portfolio.cash_balance,
            available_cash_balance=portfolio.available_cash_balance,
            reserved_cash_balance=portfolio.reserved_cash_balance,
            realized_pnl=portfolio.realized_pnl,
            equity=portfolio.equity,
            positions={
                "btc-usdt": ExternalStartupPosition(
                    instrument_id="btc-usdt",
                    quantity=portfolio.positions["btc-usdt"].quantity,
                )
            },
            order_picture={
                order_intent.order_intent_id: ExternalStartupOrderRecord(
                    order_intent_id=order_intent.order_intent_id,
                    external_order_id=accepted_report.external_order_id,
                    last_report_kind=accepted_report.kind,
                )
            },
        ),
    )

    assert isinstance(context, Wave1MtfContext)
    assert isinstance(strategy_intent, StrategyIntent)
    assert isinstance(risk_decision, RiskDecision)
    assert isinstance(order_intent, OrderIntent)
    assert isinstance(guard_outcome, GuardOutcome)
    assert isinstance(accepted_report, ExecutionReport)
    assert isinstance(fill, Fill)
    assert isinstance(position, Position)
    assert isinstance(portfolio, PortfolioState)
    assert guard_outcome.verdict is GuardVerdict.PASSED
    assert strategy_intent.metadata["entry_timeframe"] == "15m"
    assert strategy_intent.metadata["trend_timeframe"] == "1h"
    assert snapshot.last_processed_fill_id == fill.fill_id
    assert result.verdict is StartupReconciliationVerdict.CONSISTENT


def test_wave1g_minimal_core_adapter_substitution_does_not_change_upstream_logic() -> None:
    (
        _instrument,
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    ) = build_wave1g_minimal_core_pipeline()
    accepting_handoff = ExecutionHandoff(adapter=MockExecutionAdapter(accept_orders=True))
    rejecting_handoff = ExecutionHandoff(adapter=MockExecutionAdapter(accept_orders=False))

    accepting_reports = accepting_handoff.place(admitted_order)
    rejecting_reports = rejecting_handoff.place(admitted_order)

    assert isinstance(context, Wave1MtfContext)
    assert strategy_intent.side is OrderSide.BUY
    assert order_intent.quantity == risk_decision.approved_quantity
    assert order_intent.risk_decision_id == risk_decision.risk_decision_id
    assert guard_outcome.verdict is GuardVerdict.PASSED
    assert ExecutionReportKind.ACKNOWLEDGED in {report.kind for report in accepting_reports}
    assert ExecutionReportKind.REJECTED in {report.kind for report in rejecting_reports}


def test_wave1g_minimal_core_restart_restores_state_snapshot(tmp_path: Path) -> None:
    (
        _instrument,
        _context,
        _strategy_intent,
        _risk_decision,
        order_intent,
        _guard_outcome,
        admitted_order,
    ) = build_wave1g_minimal_core_pipeline()
    handoff = ExecutionHandoff(adapter=MockExecutionAdapter(accept_orders=True))
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    store_path = tmp_path / "restart" / "latest.json"
    store = JsonFileStateStore(store_path)

    reports = handoff.place(admitted_order)
    accepted_report = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    fill = handoff.materialize_fill(admitted_order, accepted_report)
    accepted_fill = fill_processor.accept(fill)
    position = position_engine.apply(None, accepted_fill)
    portfolio = portfolio_engine.apply(
        PortfolioState.empty(cash_balance=Decimal("1000")),
        accepted_fill,
        position,
    )
    store.save_with_fill_marker(
        portfolio,
        fill.fill_id,
        order_picture={
            order_intent.order_intent_id: PersistedOrderRecord(
                order_intent_id=order_intent.order_intent_id,
                external_order_id=accepted_report.external_order_id,
                last_report_kind=accepted_report.kind,
                observed_at=accepted_report.observed_at,
            )
        },
    )

    loaded_snapshot = JsonFileStateStore(store_path).load_latest()

    assert loaded_snapshot is not None
    assert loaded_snapshot.last_processed_fill_id == fill.fill_id
    assert loaded_snapshot.portfolio_state.cash_balance == portfolio.cash_balance
    assert order_intent.order_intent_id in loaded_snapshot.order_picture

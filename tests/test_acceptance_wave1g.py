from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from trading_core.context import (
    InstrumentTimeframeStore,
)
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.domain import (
    AdmittedOrder,
    ClosedBar,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReport,
    ExecutionReportKind,
    ExternalStartupBasis,
    ExternalStartupPosition,
    Fill,
    GuardOutcome,
    GuardVerdict,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    NoAction,
    OrderIntent,
    OrderSide,
    OrderType,
    PortfolioRiskBasis,
    PortfolioState,
    Position,
    RiskDecision,
    StartupReconciliationVerdict,
    StrategyIntent,
    TimeframeSyncEvent,
    TimeInForce,
    Wave1MtfContext,
)
from trading_core.execution import (
    IdempotentFillProcessor,
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.input import Wave1MtfContextAssembler
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import SpotPositionEngine
from trading_core.reconciliation import SimpleStartupReconciler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.state import JsonFileStateStore
from trading_core.strategy import BarDirectionStrategy, MtfBarAlignmentStrategy


def build_wave1g_pipeline():
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now()
    entry_bar = TimeframeSyncEvent.create(
        instrument_id="btc-usdt",
        timeframe="15m",
        bar=ClosedBar(
            timeframe="15m",
            open=Decimal("100"),
            high=Decimal("106"),
            low=Decimal("99"),
            close=Decimal("105"),
            volume=Decimal("10"),
            bar_time=now - timedelta(seconds=60),
            is_closed=True,
        ),
        received_at=now,
    )
    trend_bar = TimeframeSyncEvent.create(
        instrument_id="btc-usdt",
        timeframe="1h",
        bar=ClosedBar(
            timeframe="1h",
            open=Decimal("95"),
            high=Decimal("106"),
            low=Decimal("94"),
            close=Decimal("104"),
            volume=Decimal("40"),
            bar_time=now - timedelta(seconds=120),
            is_closed=True,
        ),
        received_at=now,
    )
    store.update(entry_bar)
    store.update(trend_bar)
    assembler = Wave1MtfContextAssembler(
        instrument=instrument,
        store=store,
        entry_timeframe="15m",
        trend_timeframe="1h",
    )
    strategy = MtfBarAlignmentStrategy(instrument=instrument)
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    builder = SimpleOrderIntentBuilder()
    guard = SimplePreExecutionGuard()
    context = assembler.assemble()
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
        (entry_bar, trend_bar),
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    )


def test_wave1g_happy_path_timeframe_context_reaches_portfolio_state() -> None:
    (
        sync_events,
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    ) = build_wave1g_pipeline()
    adapter = MockExecutionAdapter(accept_orders=True)
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    initial_portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    reports = adapter.submit(admitted_order)
    accepted_report = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    fill = adapter.materialize_fill(admitted_order, accepted_report)
    accepted_fill = fill_processor.accept(fill)
    position = position_engine.apply(None, accepted_fill)
    portfolio = portfolio_engine.apply(initial_portfolio, accepted_fill, position)

    assert len(sync_events) == 2
    assert all(isinstance(event, TimeframeSyncEvent) for event in sync_events)
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
    assert portfolio.cash_balance != initial_portfolio.cash_balance
    assert "btc-usdt" in portfolio.positions
    assert fill.order_intent_id == order_intent.order_intent_id
    assert order_intent.risk_decision_id == risk_decision.risk_decision_id
    assert risk_decision.strategy_intent_id == strategy_intent.intent_id


def test_wave1g_adapter_substitution_does_not_affect_strategy_logic() -> None:
    (
        _sync_events,
        _context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    ) = build_wave1g_pipeline()
    accepting_adapter = MockExecutionAdapter(accept_orders=True)
    rejecting_adapter = MockExecutionAdapter(accept_orders=False)

    accepting_reports = accepting_adapter.submit(admitted_order)
    rejecting_reports = rejecting_adapter.submit(admitted_order)

    assert strategy_intent.side is OrderSide.BUY
    assert order_intent.quantity == risk_decision.approved_quantity
    assert risk_decision.strategy_intent_id == strategy_intent.intent_id
    assert order_intent.risk_decision_id == risk_decision.risk_decision_id
    assert guard_outcome.verdict is GuardVerdict.PASSED
    assert ExecutionReportKind.ACKNOWLEDGED in {report.kind for report in accepting_reports}
    assert ExecutionReportKind.REJECTED in {report.kind for report in rejecting_reports}


def test_wave1g_restart_restores_state_and_passes_startup_reconciliation(
    tmp_path: Path,
) -> None:
    (
        _sync_events,
        _context,
        _strategy_intent,
        _risk_decision,
        _order_intent,
        _guard_outcome,
        admitted_order,
    ) = build_wave1g_pipeline()
    adapter = MockExecutionAdapter(accept_orders=True)
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    store_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(store_path)

    reports = adapter.submit(admitted_order)
    accepted_report = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    fill = adapter.materialize_fill(admitted_order, accepted_report)
    accepted_fill = fill_processor.accept(fill)
    position = position_engine.apply(None, accepted_fill)
    original_portfolio = portfolio_engine.apply(
        PortfolioState.empty(cash_balance=Decimal("1000")),
        accepted_fill,
        position,
    )
    store.save_with_fill_marker(original_portfolio, fill.fill_id)

    restarted_store = JsonFileStateStore(store_path)
    loaded_snapshot = restarted_store.load_latest()
    assert loaded_snapshot is not None

    external_basis = ExternalStartupBasis.create(
        cash_balance=original_portfolio.cash_balance,
        positions={
            "btc-usdt": ExternalStartupPosition(
                instrument_id="btc-usdt",
                quantity=original_portfolio.positions["btc-usdt"].quantity,
            )
        },
    )
    reconciliation_result = SimpleStartupReconciler().reconcile(loaded_snapshot, external_basis)

    assert loaded_snapshot.portfolio_state.cash_balance == original_portfolio.cash_balance
    assert loaded_snapshot.last_processed_fill_id == fill.fill_id
    assert reconciliation_result.verdict is StartupReconciliationVerdict.MATCHED


def test_wave1g_active_path_uses_mtf_strategy_not_legacy_single_bar_strategy() -> None:
    (
        _sync_events,
        context,
        strategy_intent,
        _risk_decision,
        _order_intent,
        _guard_outcome,
        _admitted_order,
    ) = build_wave1g_pipeline()

    assert isinstance(context, Wave1MtfContext)
    assert MtfBarAlignmentStrategy is not BarDirectionStrategy
    assert strategy_intent.strategy_name == "mtf_bar_alignment"


def test_wave1g_strategy_returns_no_action_when_mandatory_htf_input_missing() -> None:
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now()
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=ClosedBar(
                timeframe="15m",
                open=Decimal("100"),
                high=Decimal("106"),
                low=Decimal("99"),
                close=Decimal("105"),
                volume=Decimal("10"),
                bar_time=now - timedelta(seconds=60),
                is_closed=True,
            ),
            received_at=now,
        )
    )
    context = Wave1MtfContextAssembler(
        instrument=instrument,
        store=store,
        entry_timeframe="15m",
        trend_timeframe="1h",
    ).assemble()
    strategy = MtfBarAlignmentStrategy(instrument=instrument)

    result = strategy.evaluate(context)

    assert isinstance(result, NoAction)
    assert result.reason == "context_not_ready"

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from trading_core.context import (
    BarAlignmentPolicy,
    ClosedBarPolicy,
    ContextGate,
    FreshnessPolicy,
    InstrumentTimeframeStore,
    TimeframeContextAssembler,
)
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.domain import (
    AdmittedOrder,
    ClosedBar,
    GateVerdict,
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
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationVerdict,
    RiskDecision,
    StartupReconciliationVerdict,
    StrategyIntent,
    TimeframeSyncEvent,
    TimeInForce,
    TimeframeContext,
)
from trading_core.execution import (
    IdempotentFillProcessor,
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.governance import ActiveRuntimeContour
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import CloseIntentRouter, SpotPositionEngine
from trading_core.reconciliation import RecoveryCoordinator, SimpleStartupReconciler, SourceOfTruthPolicy
from trading_core.recovery import UnknownStateClassifier
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.state import JsonFileStateStore
from trading_core.strategy import BarDirectionStrategy, MtfBarAlignmentStrategy


def build_wave2_runtime_pipeline():
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now().replace(second=0, microsecond=0)
    trend_bar_time = now.replace(minute=0) - timedelta(hours=1)
    entry_bar_time = trend_bar_time + timedelta(minutes=45)
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
            bar_time=entry_bar_time,
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
            bar_time=trend_bar_time,
            is_closed=True,
        ),
        received_at=now,
    )
    store.update(entry_bar)
    store.update(trend_bar)
    assembler = TimeframeContextAssembler(
        instrument_id=instrument.instrument_id,
        instrument=instrument,
        store=store,
        alignment_policy=BarAlignmentPolicy(
            entry_timeframe="15m",
            required_timeframes=("15m", "1h"),
        ),
        closed_bar_policy=ClosedBarPolicy(),
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
    )
    gate = ContextGate(
        warmup_bars=1,
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
        required_timeframes=("15m", "1h"),
    )
    strategy = MtfBarAlignmentStrategy()
    classifier = UnknownStateClassifier()
    recovery = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    runtime = ActiveRuntimeContour(
        context_provider=assembler,
        gate=gate,
        strategy=strategy,
        classifier=classifier,
        recovery_coordinator=recovery,
    )
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    builder = SimpleOrderIntentBuilder()
    guard = SimplePreExecutionGuard()
    cycle = runtime.run_cycle()
    context = cycle.context
    strategy_intent = cycle.strategy_result
    assert cycle.gate_outcome is not None
    assert cycle.gate_outcome.verdict is GateVerdict.ADMITTED
    assert isinstance(context, TimeframeContext)
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
        (entry_bar, trend_bar),
        runtime,
        classifier,
        cycle,
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    )


def test_wave1g_happy_path_timeframe_context_reaches_portfolio_state() -> None:
    (
        _instrument,
        sync_events,
        runtime,
        _classifier,
        cycle,
        context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    ) = build_wave2_runtime_pipeline()
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
    assert isinstance(context, TimeframeContext)
    assert cycle.gate_outcome is not None
    assert cycle.gate_outcome.verdict is GateVerdict.ADMITTED
    assert cycle.strategy_result == strategy_intent
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
    assert runtime.classifier.is_trading_allowed() is True


def test_wave1g_adapter_substitution_does_not_affect_strategy_logic() -> None:
    (
        _instrument,
        _sync_events,
        _runtime,
        _classifier,
        _cycle,
        _context,
        strategy_intent,
        risk_decision,
        order_intent,
        guard_outcome,
        admitted_order,
    ) = build_wave2_runtime_pipeline()
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
        _instrument,
        _sync_events,
        runtime,
        _classifier,
        _cycle,
        _context,
        _strategy_intent,
        _risk_decision,
        _order_intent,
        _guard_outcome,
        admitted_order,
    ) = build_wave2_runtime_pipeline()
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
    startup_request = runtime.request_startup_reconciliation("btc-usdt")

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
    assert startup_request.mode is ReconciliationMode.STARTUP
    assert reconciliation_result.verdict is StartupReconciliationVerdict.CONSISTENT


def test_wave1g_active_runtime_uses_timeframe_context_and_mtf_strategy() -> None:
    (
        _instrument,
        _sync_events,
        runtime,
        _classifier,
        cycle,
        context,
        strategy_intent,
        _risk_decision,
        _order_intent,
        _guard_outcome,
        _admitted_order,
    ) = build_wave2_runtime_pipeline()

    assert isinstance(context, TimeframeContext)
    assert MtfBarAlignmentStrategy is not BarDirectionStrategy
    assert runtime.gate is not None
    assert cycle.gate_outcome is not None
    assert cycle.gate_outcome.verdict is GateVerdict.ADMITTED
    assert strategy_intent.strategy_name == "mtf_bar_alignment"


def test_wave1g_gate_blocks_cycle_when_mandatory_htf_input_missing() -> None:
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
    runtime = ActiveRuntimeContour(
        context_provider=TimeframeContextAssembler(
            instrument_id=instrument.instrument_id,
            instrument=instrument,
            store=store,
            alignment_policy=BarAlignmentPolicy(
                entry_timeframe="15m",
                required_timeframes=("15m", "1h"),
            ),
            closed_bar_policy=ClosedBarPolicy(),
            freshness_policy=FreshnessPolicy(max_age_seconds=7200),
        ),
        gate=ContextGate(
            warmup_bars=1,
            freshness_policy=FreshnessPolicy(max_age_seconds=7200),
            required_timeframes=("15m", "1h"),
        ),
        strategy=MtfBarAlignmentStrategy(),
        classifier=UnknownStateClassifier(),
        recovery_coordinator=RecoveryCoordinator(
            source_of_truth=SourceOfTruthPolicy(),
            classifier=UnknownStateClassifier(),
        ),
    )

    cycle = runtime.run_cycle()

    assert cycle.context is not None
    assert cycle.gate_outcome is not None
    assert cycle.gate_outcome.reason is not None
    assert cycle.gate_outcome.verdict is GateVerdict.DEFERRED
    assert cycle.strategy_result is None


def test_wave1g_unknown_state_posture_blocks_active_runtime_cycle() -> None:
    (
        _instrument,
        _sync_events,
        runtime,
        classifier,
        _cycle,
        _context,
        _strategy_intent,
        _risk_decision,
        _order_intent,
        _guard_outcome,
        _admitted_order,
    ) = build_wave2_runtime_pipeline()
    transition = runtime.process_reconciliation_outcome(
        ReconciliationOutcome.create(
            request_id="recon_req_123",
            mode=ReconciliationMode.ON_ERROR,
            verdict=ReconciliationVerdict.INSUFFICIENT,
            conflicts_with_active_trading=False,
            reason="external_basis_insufficient",
            instrument_id="btc-usdt",
        )
    )

    blocked_cycle = runtime.run_cycle()

    assert transition is not None
    assert classifier.is_trading_allowed() is False
    assert blocked_cycle.blocked_by_system_posture is True
    assert blocked_cycle.strategy_result is None


def test_wave1g_close_route_failure_escalation_blocks_following_runtime_cycle() -> None:
    (
        instrument,
        _sync_events,
        runtime,
        classifier,
        _cycle,
        _context,
        _strategy_intent,
        _risk_decision,
        _order_intent,
        _guard_outcome,
        _admitted_order,
    ) = build_wave2_runtime_pipeline()
    close_router = CloseIntentRouter(
        order_builder=SimpleOrderIntentBuilder(),
        pre_execution_guard=SimplePreExecutionGuard(),
        execution_coordinator=MockExecutionAdapter(accept_orders=True),
        classifier=classifier,
    )
    close_result = close_router.route(
        close_intent=SpotPositionEngine().initiate_close(
            Position(
                position_id="pos_123",
                instrument=instrument,
                quantity=Decimal("0.20"),
                average_entry_price=Decimal("100"),
                realized_pnl=Decimal("0"),
                updated_at=PortfolioState.empty(cash_balance=Decimal("1000")).updated_at,
                metadata={},
            ),
            quantity=Decimal("0.105"),
            reason="protective_close",
        ),
        current_position_quantity=Decimal("0.20"),
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.001"),
            price_step=Decimal("0.10"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
        admissibility_basis=ExecutionAdmissibilityBasis(
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

    blocked_cycle = runtime.run_cycle()

    assert close_result.verdict.value == "guard_rejected"
    assert classifier.is_trading_allowed() is False
    assert blocked_cycle.blocked_by_system_posture is True

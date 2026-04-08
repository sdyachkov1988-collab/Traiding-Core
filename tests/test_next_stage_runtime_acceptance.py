from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from trading_core.context import (
    BarAlignmentPolicy,
    ClosedBarPolicy,
    ContextGate,
    FreshnessPolicy,
    InstrumentTimeframeStore,
    TimeframeContextAssembler,
)
from trading_core.domain import (
    AdmittedOrder,
    ClosedBar,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReportKind,
    GateVerdict,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    OrderType,
    PortfolioRiskBasis,
    PortfolioState,
    Position,
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationVerdict,
    TimeInForce,
    TimeframeContext,
    TimeframeSyncEvent,
)
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.execution import (
    ExecutionHandoff,
    IdempotentFillProcessor,
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.governance import ActiveRuntimeContour
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import CloseIntentRouter, SpotPositionEngine
from trading_core.reconciliation import RecoveryCoordinator, SourceOfTruthPolicy
from trading_core.recovery import UnknownStateClassifier
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.strategy import MtfBarAlignmentStrategy


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
    classifier = UnknownStateClassifier()
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
        classifier=classifier,
        recovery_coordinator=RecoveryCoordinator(
            source_of_truth=SourceOfTruthPolicy(),
            classifier=classifier,
        ),
    )
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    builder = SimpleOrderIntentBuilder()
    guard = SimplePreExecutionGuard()
    cycle = runtime.run_cycle()
    assert cycle.context is not None
    assert cycle.strategy_result is not None
    risk_decision = risk.evaluate(
        intent=cycle.strategy_result,
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
    admitted_order = AdmittedOrder.create(
        order_intent=order_intent,
        guard_outcome=guard_outcome,
    )
    return instrument, runtime, cycle, admitted_order


def test_next_stage_runtime_contour_reaches_portfolio_state() -> None:
    _instrument, runtime, cycle, admitted_order = build_wave2_runtime_pipeline()
    handoff = ExecutionHandoff(adapter=MockExecutionAdapter(accept_orders=True))
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()

    assert isinstance(cycle.context, TimeframeContext)
    assert cycle.gate_outcome is not None
    assert cycle.gate_outcome.verdict is GateVerdict.ADMITTED
    reports = handoff.place(admitted_order)
    accepted_report = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    fill = handoff.materialize_fill(admitted_order, accepted_report)
    position = position_engine.apply(None, fill_processor.accept(fill))
    portfolio = portfolio_engine.apply(PortfolioState.empty(cash_balance=Decimal("1000")), fill, position)

    assert portfolio.cash_balance != Decimal("1000")
    assert "btc-usdt" in portfolio.positions
    assert runtime.classifier.is_trading_allowed() is True


def test_next_stage_runtime_gate_blocks_cycle_when_mandatory_htf_input_missing() -> None:
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
    assert cycle.gate_outcome.verdict is GateVerdict.DEFERRED
    assert cycle.strategy_result is None


def test_next_stage_runtime_unknown_state_posture_blocks_runtime_cycle() -> None:
    _instrument, runtime, _cycle, _admitted_order = build_wave2_runtime_pipeline()
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
    assert runtime.classifier.is_trading_allowed() is False
    assert blocked_cycle.blocked_by_system_posture is True
    assert blocked_cycle.strategy_result is None


def test_next_stage_runtime_close_route_failure_blocks_following_cycle() -> None:
    instrument, runtime, _cycle, _admitted_order = build_wave2_runtime_pipeline()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    current_position = Position(
        position_id="pos_123",
        instrument=instrument,
        quantity=Decimal("0.20"),
        average_entry_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        updated_at=portfolio.updated_at,
        metadata={},
    )
    close_router = CloseIntentRouter(
        order_builder=SimpleOrderIntentBuilder(),
        pre_execution_guard=SimplePreExecutionGuard(),
        execution_coordinator=MockExecutionAdapter(accept_orders=True),
        classifier=runtime.classifier,
    )
    close_result = close_router.route(
        close_intent=SpotPositionEngine().initiate_close(
            current_position,
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
    assert runtime.classifier.is_trading_allowed() is False
    assert blocked_cycle.blocked_by_system_posture is True

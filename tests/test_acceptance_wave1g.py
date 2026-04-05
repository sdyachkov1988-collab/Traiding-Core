from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from trading_core.domain import (
    AdmittedOrder,
    EventKind,
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
    MarketContext,
    MarketEvent,
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
)
from trading_core.execution import (
    IdempotentFillProcessor,
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.input import DictEventNormalizer, SimpleMarketContextAssembler
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import SpotPositionEngine
from trading_core.reconciliation import SimpleStartupReconciler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.state import JsonFileStateStore
from trading_core.strategy import BarDirectionStrategy


def build_wave1g_pipeline():
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

    market_event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {
                "timeframe": "15m",
                "open": "100",
                "close": "105",
            },
        }
    )
    context = assembler.assemble(market_event)
    strategy_intent = strategy.evaluate(context)
    risk_decision = risk.evaluate(
        intent=strategy_intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("10"),
            max_capital_per_trade=Decimal("5"),
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
    return market_event, context, strategy_intent, risk_decision, order_intent, guard_outcome, admitted_order


def test_wave1g_happy_path_market_event_reaches_portfolio_state() -> None:
    (
        market_event,
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
    fill = Fill.create(
        order_intent_id=admitted_order.order_intent.order_intent_id,
        instrument=admitted_order.order_intent.instrument,
        side=admitted_order.order_intent.side,
        quantity=admitted_order.order_intent.quantity,
        price=admitted_order.order_intent.limit_price or Decimal("105.00"),
        fee=Decimal("0"),
        external_fill_id=accepted_report.external_order_id,
    )
    accepted_fill = fill_processor.accept(fill)
    position = position_engine.apply(None, accepted_fill)
    portfolio = portfolio_engine.apply(initial_portfolio, accepted_fill, position)

    assert isinstance(market_event, MarketEvent)
    assert isinstance(context, MarketContext)
    assert isinstance(strategy_intent, StrategyIntent)
    assert isinstance(risk_decision, RiskDecision)
    assert isinstance(order_intent, OrderIntent)
    assert isinstance(guard_outcome, GuardOutcome)
    assert isinstance(accepted_report, ExecutionReport)
    assert isinstance(position, Position)
    assert isinstance(portfolio, PortfolioState)
    assert guard_outcome.verdict is GuardVerdict.PASSED
    assert portfolio.cash_balance != initial_portfolio.cash_balance
    assert "btc-usdt" in portfolio.positions
    assert fill.order_intent_id == order_intent.order_intent_id
    assert order_intent.risk_decision_id == risk_decision.risk_decision_id
    assert risk_decision.strategy_intent_id == strategy_intent.intent_id


def test_wave1g_adapter_substitution_does_not_affect_strategy_logic() -> None:
    (
        _market_event,
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
        _market_event,
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
    fill = Fill.create(
        order_intent_id=admitted_order.order_intent.order_intent_id,
        instrument=admitted_order.order_intent.instrument,
        side=admitted_order.order_intent.side,
        quantity=admitted_order.order_intent.quantity,
        price=admitted_order.order_intent.limit_price or Decimal("105.00"),
        fee=Decimal("0"),
        external_fill_id=accepted_report.external_order_id,
    )
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

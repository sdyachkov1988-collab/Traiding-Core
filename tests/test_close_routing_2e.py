from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from trading_core.contracts.close_router import CloseIntentRouterProtocol
from trading_core.contracts.execution import ExecutionAdapter
from trading_core.domain import (
    AdmittedOrder,
    CloseIntent,
    CloseRoutingResult,
    CloseRoutingVerdict,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReport,
    ExecutionReportKind,
    InstrumentExecutionSpec,
    InstrumentRef,
    OrderType,
    PortfolioState,
    SystemMode,
    TimeInForce,
)
from trading_core.execution import MockExecutionAdapter, SimpleOrderIntentBuilder, SimplePreExecutionGuard
from trading_core.positions import CloseIntentRouter, SpotPositionEngine
from trading_core.domain.portfolio_state import Position
from trading_core.recovery import UnknownStateClassifier


class PendingExecutionAdapter:
    """Adapter stub that never returns final execution confirmation."""

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        return (
            ExecutionReport.create(
                kind=ExecutionReportKind.SUBMITTED,
                order_intent_id=admitted_order.order_intent.order_intent_id,
                metadata={"admitted_order_id": admitted_order.admitted_order_id},
            ),
        )


class RecordingExecutionAdapter:
    """Adapter spy used to prove the close route reaches the execution boundary."""

    def __init__(self) -> None:
        self.submitted_order_ids: list[str] = []
        self.submitted_orders: list[AdmittedOrder] = []
        self._delegate = MockExecutionAdapter(accept_orders=True)

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        self.submitted_order_ids.append(admitted_order.admitted_order_id)
        self.submitted_orders.append(admitted_order)
        return self._delegate.submit(admitted_order)


def instrument() -> InstrumentRef:
    return InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )


def instrument_spec() -> InstrumentExecutionSpec:
    return InstrumentExecutionSpec(
        instrument_id="btc-usdt",
        quantity_step=Decimal("0.01"),
        price_step=Decimal("0.10"),
        supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
        supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
    )


def permissive_builder_spec() -> InstrumentExecutionSpec:
    return InstrumentExecutionSpec(
        instrument_id="btc-usdt",
        quantity_step=Decimal("0.001"),
        price_step=Decimal("0.10"),
        supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
        supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
    )


def execution_basis() -> ExecutionConstraintBasis:
    return ExecutionConstraintBasis(
        reference_price=Decimal("105.00"),
        preferred_limit_offset=Decimal("0.20"),
    )


def admissibility_basis() -> ExecutionAdmissibilityBasis:
    return ExecutionAdmissibilityBasis(
        instrument_id="btc-usdt",
        quantity_step=Decimal("0.01"),
        price_step=Decimal("0.10"),
        min_quantity=Decimal("0.01"),
        min_notional=Decimal("1"),
        supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
        supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        reference_price=Decimal("105.00"),
    )


def router_with_classifier(
    execution_coordinator: ExecutionAdapter | None = None,
) -> tuple[CloseIntentRouter, UnknownStateClassifier]:
    classifier = UnknownStateClassifier()
    router = CloseIntentRouter(
        order_builder=SimpleOrderIntentBuilder(),
        pre_execution_guard=SimplePreExecutionGuard(),
        execution_coordinator=execution_coordinator or MockExecutionAdapter(accept_orders=True),
        classifier=classifier,
    )
    return router, classifier


def test_close_intent_is_created_with_correct_types() -> None:
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    assert close_intent.intent_id.startswith("close_")
    assert close_intent.instrument.instrument_id == "btc-usdt"
    assert close_intent.quantity == Decimal("0.10")
    assert close_intent.created_at.tzinfo == timezone.utc


def test_valid_close_intent_is_admitted_by_router() -> None:
    router, _ = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.10"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.ADMITTED
    assert result.admitted_order_id is not None


def test_position_engine_can_initiate_close_intent_without_new_strategy_signal() -> None:
    position_engine = SpotPositionEngine()
    current_position = Position(
        position_id="pos_123",
        instrument=instrument(),
        quantity=Decimal("0.25"),
        average_entry_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        updated_at=PortfolioState.empty(cash_balance=Decimal("1000")).updated_at,
        metadata={},
    )

    close_intent = position_engine.initiate_close(
        current_position,
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    assert close_intent.position_id == current_position.position_id
    assert close_intent.quantity == Decimal("0.10")
    assert close_intent.instrument.instrument_id == current_position.instrument.instrument_id


def test_close_route_reaches_execution_boundary_only_through_normal_path() -> None:
    execution_coordinator = RecordingExecutionAdapter()
    router, _ = router_with_classifier(execution_coordinator)
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.10"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.ADMITTED
    assert execution_coordinator.submitted_order_ids == [result.admitted_order_id]


def test_close_route_does_not_fake_strategy_or_risk_lineage() -> None:
    execution_coordinator = RecordingExecutionAdapter()
    router, _ = router_with_classifier(execution_coordinator)
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.10"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    submitted_order = execution_coordinator.submitted_orders[0]

    assert result.verdict == CloseRoutingVerdict.ADMITTED
    assert submitted_order.order_intent.risk_decision_id is None
    assert submitted_order.order_intent.metadata["origin"] == "position_close"
    assert submitted_order.order_intent.metadata["close_intent_id"] == close_intent.intent_id
    assert "strategy_intent_id" not in submitted_order.order_intent.metadata


def test_invalid_close_quantity_triggers_safe_mode_path() -> None:
    router, classifier = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.105"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.20"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.GUARD_REJECTED
    assert result.reason == "quantity_rounding_invalid"
    assert classifier.current_mode == SystemMode.NORMAL


def test_guard_reject_never_results_in_silent_failure() -> None:
    router, _ = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.001"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.001"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert isinstance(result, CloseRoutingResult)
    assert result.verdict == CloseRoutingVerdict.GUARD_REJECTED
    assert result.reason is not None


def test_close_routing_result_preserves_lineage() -> None:
    router, _ = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.10"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.close_intent_id == close_intent.intent_id


def test_guard_reject_remains_guard_level_outcome() -> None:
    router, classifier = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.105"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.20"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.GUARD_REJECTED
    assert classifier.is_trading_allowed() is True
    assert classifier.current_mode == SystemMode.NORMAL


def test_close_intent_router_matches_protocol() -> None:
    router, _ = router_with_classifier()

    assert isinstance(router, CloseIntentRouterProtocol)


def test_close_router_rejects_when_no_position_is_available() -> None:
    router, classifier = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.REJECTED
    assert result.reason == "no_position_to_close"
    assert classifier.current_mode == SystemMode.NORMAL


def test_execution_reject_on_close_route_remains_execution_level_outcome() -> None:
    router, classifier = router_with_classifier(MockExecutionAdapter(accept_orders=False))
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.10"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.EXECUTION_REJECTED
    assert result.reason == "adapter_rejected_submission"
    assert classifier.current_mode == SystemMode.NORMAL


def test_missing_execution_confirmation_on_close_route_triggers_explicit_reconcile_path() -> None:
    router, classifier = router_with_classifier(PendingExecutionAdapter())
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.10"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        current_position_quantity=Decimal("0.10"),
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.RECONCILE_REQUIRED
    assert result.reason == "execution_confirmation_missing"
    assert classifier.current_mode == SystemMode.READ_ONLY
    assert classifier.is_trading_allowed() is False


def test_close_intent_rejects_naive_created_at_datetime() -> None:
    try:
        CloseIntent(
            intent_id="close_123",
            instrument=instrument(),
            position_id="pos_123",
            quantity=Decimal("0.10"),
            reason="protective_close",
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )
    except ValueError as exc:
        assert str(exc) == "created_at must be timezone-aware UTC"
    else:
        raise AssertionError("Expected naive created_at to be rejected")

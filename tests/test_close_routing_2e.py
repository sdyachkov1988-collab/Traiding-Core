from __future__ import annotations

from datetime import timezone
from decimal import Decimal

from trading_core.contracts.close_router import CloseIntentRouterProtocol
from trading_core.domain import (
    CloseIntent,
    CloseRoutingResult,
    CloseRoutingVerdict,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    InstrumentExecutionSpec,
    InstrumentRef,
    OrderType,
    SystemMode,
    TimeInForce,
)
from trading_core.execution import SimpleOrderIntentBuilder, SimplePreExecutionGuard
from trading_core.positions import CloseIntentRouter
from trading_core.recovery import UnknownStateClassifier


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


def router_with_classifier() -> tuple[CloseIntentRouter, UnknownStateClassifier]:
    classifier = UnknownStateClassifier()
    router = CloseIntentRouter(
        order_builder=SimpleOrderIntentBuilder(),
        pre_execution_guard=SimplePreExecutionGuard(),
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
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.ADMITTED
    assert result.admitted_order_id is not None


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
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict in (
        CloseRoutingVerdict.REJECTED,
        CloseRoutingVerdict.SAFE_MODE_TRIGGERED,
    )
    assert result.reason == "quantity_rounding_invalid"
    assert classifier.current_mode == SystemMode.SAFE_MODE


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
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert isinstance(result, CloseRoutingResult)
    assert result.verdict in (
        CloseRoutingVerdict.REJECTED,
        CloseRoutingVerdict.SAFE_MODE_TRIGGERED,
    )


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
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.close_intent_id == close_intent.intent_id


def test_router_classifies_unknown_state_after_guard_reject() -> None:
    router, classifier = router_with_classifier()
    close_intent = CloseIntent.create(
        instrument=instrument(),
        position_id="pos_123",
        quantity=Decimal("0.105"),
        reason="protective_close",
    )

    result = router.route(
        close_intent=close_intent,
        instrument_spec=permissive_builder_spec(),
        execution_basis=execution_basis(),
        admissibility_basis=admissibility_basis(),
    )

    assert result.verdict == CloseRoutingVerdict.SAFE_MODE_TRIGGERED
    assert classifier.is_trading_allowed() is False
    assert classifier.current_mode == SystemMode.SAFE_MODE


def test_close_intent_router_matches_protocol() -> None:
    router, _ = router_with_classifier()

    assert isinstance(router, CloseIntentRouterProtocol)

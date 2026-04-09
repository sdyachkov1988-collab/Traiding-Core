"""Order-intent builders for D1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.close_intent import CloseIntent
from trading_core.domain.instruments import ExecutionConstraintBasis, InstrumentExecutionSpec
from trading_core.domain.orders import OrderIntent, OrderSide, OrderType, TimeInForce
from trading_core.domain.risk import RiskDecision, RiskVerdict
from trading_core.observability import emit_structured_event


@dataclass(slots=True)
class SimpleOrderIntentBuilder:
    """Build an order intent from an approved risk decision only."""

    def build(
        self,
        decision: RiskDecision,
        instrument_spec: InstrumentExecutionSpec,
        execution_basis: ExecutionConstraintBasis,
    ) -> OrderIntent:
        """Return only the order form, without guard or execution concerns."""

        if decision.verdict not in (RiskVerdict.APPROVED, RiskVerdict.CAPPED):
            raise ValueError("OrderIntentBuilder requires an approved or capped RiskDecision")
        if decision.approved_quantity is None:
            raise ValueError("Approved RiskDecision must contain approved_quantity")
        if decision.instrument.instrument_id != instrument_spec.instrument_id:
            raise ValueError("Instrument spec does not match RiskDecision instrument")

        order_type = self._choose_order_type(instrument_spec)
        time_in_force = self._choose_time_in_force(instrument_spec)
        side = decision.side
        quantity = self._align_down_to_step(
            decision.approved_quantity,
            instrument_spec.quantity_step,
        )
        if quantity < instrument_spec.min_order_quantity:
            raise ValueError("Rounded quantity fell below instrument minimum quantity")
        limit_price = None
        if order_type is OrderType.LIMIT:
            limit_price = self._build_limit_price(
                reference_price=execution_basis.reference_price,
                offset=execution_basis.preferred_limit_offset,
                price_step=instrument_spec.price_step,
                side=side,
            )

        order_intent = OrderIntent.create(
            risk_decision_id=decision.risk_decision_id,
            instrument=decision.instrument,
            side=side,
            order_type=order_type,
            quantity=quantity,
            time_in_force=time_in_force,
            limit_price=limit_price,
            metadata={"strategy_intent_id": decision.strategy_intent_id},
        )
        emit_structured_event(
            logger_name=__name__,
            event_type="order_intent",
            entity_type="order_intent",
            entity_id=order_intent.order_intent_id,
            lineage_id=decision.risk_decision_id,
            stage="execution_preparation",
            lifecycle_step="order_intent_built",
            decision="build_order_intent",
            outcome="created",
            reason=decision.verdict.value,
            reason_code=decision.verdict.value,
            metadata={"instrument_id": order_intent.instrument.instrument_id},
        )
        return order_intent

    def build_close_order(
        self,
        close_intent: CloseIntent,
        instrument_spec: InstrumentExecutionSpec,
        execution_basis: ExecutionConstraintBasis,
    ) -> OrderIntent:
        """Build an order intent for a position-originated close route without fake strategy/risk lineage."""

        if close_intent.instrument.instrument_id != instrument_spec.instrument_id:
            raise ValueError("Instrument spec does not match CloseIntent instrument")
        order_type = self._choose_order_type(instrument_spec)
        time_in_force = self._choose_time_in_force(instrument_spec)
        quantity = self._align_down_to_step(
            close_intent.quantity,
            instrument_spec.quantity_step,
        )
        if quantity < instrument_spec.min_order_quantity:
            raise ValueError("Rounded quantity fell below instrument minimum quantity")
        limit_price = None
        if order_type is OrderType.LIMIT:
            limit_price = self._build_limit_price(
                reference_price=execution_basis.reference_price,
                offset=execution_basis.preferred_limit_offset,
                price_step=instrument_spec.price_step,
                side=OrderSide.SELL,
            )

        return OrderIntent.create(
            risk_decision_id=None,
            instrument=close_intent.instrument,
            side=OrderSide.SELL,
            order_type=order_type,
            quantity=quantity,
            time_in_force=time_in_force,
            limit_price=limit_price,
            metadata={
                "origin": "position_close",
                "close_intent_id": close_intent.intent_id,
                "position_id": close_intent.position_id,
                "close_reason": close_intent.reason,
            },
        )

    def _choose_order_type(self, instrument_spec: InstrumentExecutionSpec) -> OrderType:
        if instrument_spec.default_order_type not in instrument_spec.supported_order_types:
            raise ValueError("Default order type is not supported by instrument spec")
        return instrument_spec.default_order_type

    def _choose_time_in_force(self, instrument_spec: InstrumentExecutionSpec) -> TimeInForce:
        if instrument_spec.default_time_in_force not in instrument_spec.supported_time_in_force:
            raise ValueError("Default time in force is not supported by instrument spec")
        return instrument_spec.default_time_in_force

    def _build_limit_price(
        self,
        *,
        reference_price: Decimal,
        offset: Decimal,
        price_step: Decimal,
        side: OrderSide,
    ) -> Decimal:
        """Build an aggressive taker-oriented limit price.

        BUY limits are placed above the reference price to increase the chance
        of immediate execution. SELL limits are placed below the reference
        price for the same reason. An offset of zero places the limit exactly
        at the reference price.
        """

        signed_offset = offset if side is OrderSide.BUY else -offset
        limit_price = self._align_down_to_step(
            reference_price + signed_offset,
            price_step,
        )
        if limit_price <= Decimal("0"):
            raise ValueError("Limit price must be positive")
        return limit_price

    def _align_down_to_step(
        self,
        value: Decimal,
        step: Decimal,
    ) -> Decimal:
        return (value // step) * step

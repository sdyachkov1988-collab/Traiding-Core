"""Position-originated close-routing contour for Wave 2E."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.contracts.guards import PreExecutionGuard
from trading_core.contracts.orders import OrderIntentBuilder
from trading_core.domain.close_intent import CloseIntent, CloseRoutingResult, CloseRoutingVerdict
from trading_core.domain.execution import AdmittedOrder
from trading_core.domain.guards import ExecutionAdmissibilityBasis, GuardVerdict
from trading_core.domain.instruments import ExecutionConstraintBasis, InstrumentExecutionSpec
from trading_core.domain.orders import OrderSide
from trading_core.domain.risk import RiskDecision, RiskVerdict
from trading_core.recovery import UnknownStateClassifier


@dataclass(slots=True)
class CloseIntentRouter:
    """Route close intents through the normal builder and guard seams."""

    order_builder: OrderIntentBuilder
    pre_execution_guard: PreExecutionGuard
    classifier: UnknownStateClassifier

    def route(
        self,
        close_intent: CloseIntent,
        current_position_quantity: Decimal,
        instrument_spec: InstrumentExecutionSpec,
        execution_basis: ExecutionConstraintBasis,
        admissibility_basis: ExecutionAdmissibilityBasis,
    ) -> CloseRoutingResult:
        """Return an explicit routing outcome for a position-originated close intent."""

        if current_position_quantity <= Decimal("0"):
            return self._trigger_safe_mode(
                close_intent=close_intent,
                reason="no_position_to_close",
            )
        if close_intent.quantity > current_position_quantity:
            return self._trigger_safe_mode(
                close_intent=close_intent,
                reason="close_quantity_exceeds_current_position_quantity",
            )

        # Minimal Core v1 position routing is spot-oriented: closing a live
        # position means reducing it with a SELL order through the normal seams.
        decision = RiskDecision.create(
            verdict=RiskVerdict.APPROVED,
            strategy_intent_id=close_intent.intent_id,
            instrument=close_intent.instrument,
            side=OrderSide.SELL,
            approved_quantity=close_intent.quantity,
            metadata={
                "origin": "position_close",
                "position_id": close_intent.position_id,
                "close_reason": close_intent.reason,
            },
        )
        order_intent = self.order_builder.build(
            decision=decision,
            instrument_spec=instrument_spec,
            execution_basis=execution_basis,
        )
        guard_outcome = self.pre_execution_guard.check(
            intent=order_intent,
            basis=admissibility_basis,
        )
        if guard_outcome.verdict is GuardVerdict.PASSED:
            admitted_order = AdmittedOrder.create(
                order_intent=order_intent,
                guard_outcome=guard_outcome,
                metadata={
                    "close_intent_id": close_intent.intent_id,
                    "position_id": close_intent.position_id,
                },
            )
            return CloseRoutingResult.create(
                close_intent_id=close_intent.intent_id,
                verdict=CloseRoutingVerdict.ADMITTED,
                order_intent_id=order_intent.order_intent_id,
                admitted_order_id=admitted_order.admitted_order_id,
            )

        return self._trigger_safe_mode(
            close_intent=close_intent,
            reason=guard_outcome.reason or "close_routing_guard_rejected",
            order_intent_id=order_intent.order_intent_id,
        )

    def _trigger_safe_mode(
        self,
        *,
        close_intent: CloseIntent,
        reason: str,
        order_intent_id: str | None = None,
    ) -> CloseRoutingResult:
        """Classify an unknown position path and return an explicit safe-mode result."""

        _, transition = self.classifier.classify_unknown_position(
            instrument_id=close_intent.instrument.instrument_id,
            reason=reason,
        )
        self.classifier.apply_transition(transition)
        return CloseRoutingResult.create(
            close_intent_id=close_intent.intent_id,
            verdict=CloseRoutingVerdict.SAFE_MODE_TRIGGERED,
            order_intent_id=order_intent_id,
            reason=reason,
        )

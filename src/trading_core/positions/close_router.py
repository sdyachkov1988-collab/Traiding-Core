"""Position-originated close-routing contour for Wave 2E."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.contracts.execution import ExecutionSubmitter
from trading_core.contracts.guards import PreExecutionGuard
from trading_core.contracts.orders import OrderIntentBuilder
from trading_core.contracts.recovery import UnknownStateClassifierProtocol
from trading_core.domain.close_intent import CloseIntent, CloseRoutingResult, CloseRoutingVerdict
from trading_core.domain.execution import AdmittedOrder, ExecutionReportKind
from trading_core.domain.guards import ExecutionAdmissibilityBasis, GuardVerdict
from trading_core.domain.instruments import ExecutionConstraintBasis, InstrumentExecutionSpec


@dataclass(slots=True)
class CloseIntentRouter:
    """Route close intents through the normal builder and guard seams."""

    order_builder: OrderIntentBuilder
    pre_execution_guard: PreExecutionGuard
    execution_coordinator: ExecutionSubmitter
    classifier: UnknownStateClassifierProtocol

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
            return CloseRoutingResult.create(
                close_intent_id=close_intent.intent_id,
                verdict=CloseRoutingVerdict.REJECTED,
                reason="no_position_to_close",
            )
        if close_intent.quantity > current_position_quantity:
            return CloseRoutingResult.create(
                close_intent_id=close_intent.intent_id,
                verdict=CloseRoutingVerdict.REJECTED,
                reason="close_quantity_exceeds_current_position_quantity",
            )

        try:
            order_intent = self.order_builder.build_close_order(
                close_intent=close_intent,
                instrument_spec=instrument_spec,
                execution_basis=execution_basis,
            )
        except ValueError as exc:
            return CloseRoutingResult.create(
                close_intent_id=close_intent.intent_id,
                verdict=CloseRoutingVerdict.REJECTED,
                reason=str(exc),
            )
        guard_outcome = self.pre_execution_guard.check(
            intent=order_intent,
            basis=admissibility_basis,
        )
        if guard_outcome.verdict is not GuardVerdict.PASSED:
            return CloseRoutingResult.create(
                close_intent_id=close_intent.intent_id,
                verdict=CloseRoutingVerdict.GUARD_REJECTED,
                order_intent_id=order_intent.order_intent_id,
                reason=guard_outcome.reason or "close_routing_guard_rejected",
            )

        admitted_order = AdmittedOrder.create(
            order_intent=order_intent,
            guard_outcome=guard_outcome,
            metadata={
                "close_intent_id": close_intent.intent_id,
                "position_id": close_intent.position_id,
            },
        )
        reports = self.execution_coordinator.submit(admitted_order)
        if any(report.kind is ExecutionReportKind.REJECTED for report in reports):
            return CloseRoutingResult.create(
                close_intent_id=close_intent.intent_id,
                verdict=CloseRoutingVerdict.EXECUTION_REJECTED,
                order_intent_id=order_intent.order_intent_id,
                admitted_order_id=admitted_order.admitted_order_id,
                reason=next(
                    (
                        report.reason
                        for report in reports
                        if report.kind is ExecutionReportKind.REJECTED
                        and report.reason is not None
                    ),
                    "close_execution_rejected",
                ),
            )
        if not any(
            report.kind in (ExecutionReportKind.ACCEPTED, ExecutionReportKind.ACKNOWLEDGED)
            for report in reports
        ):
            return self._trigger_reconcile_path(
                close_intent=close_intent,
                reason="execution_confirmation_missing",
                order_intent_id=order_intent.order_intent_id,
                admitted_order_id=admitted_order.admitted_order_id,
            )
        return CloseRoutingResult.create(
            close_intent_id=close_intent.intent_id,
            verdict=CloseRoutingVerdict.ADMITTED,
            order_intent_id=order_intent.order_intent_id,
            admitted_order_id=admitted_order.admitted_order_id,
        )

    def _trigger_reconcile_path(
        self,
        *,
        close_intent: CloseIntent,
        reason: str,
        order_intent_id: str,
        admitted_order_id: str,
    ) -> CloseRoutingResult:
        """Classify incomplete execution confirmation as an explicit reconcile-required path."""

        _, transition = self.classifier.classify_missing_execution_confirmation(
            order_intent_id=order_intent_id,
            instrument_id=close_intent.instrument.instrument_id,
        )
        self.classifier.apply_transition(transition)
        return CloseRoutingResult.create(
            close_intent_id=close_intent.intent_id,
            verdict=CloseRoutingVerdict.RECONCILE_REQUIRED,
            order_intent_id=order_intent_id,
            admitted_order_id=admitted_order_id,
            reason=reason,
        )

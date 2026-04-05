"""Pre-execution guard implementations for D2."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.guards import ExecutionAdmissibilityBasis, GuardOutcome, GuardVerdict
from trading_core.domain.orders import OrderIntent, OrderType


@dataclass(slots=True)
class SimplePreExecutionGuard:
    """Run formal admissibility checks before crossing the execution boundary."""

    def check(
        self,
        intent: OrderIntent,
        basis: ExecutionAdmissibilityBasis,
    ) -> GuardOutcome:
        """Return a formal pass/reject outcome without building an external order."""

        if intent.instrument.instrument_id != basis.instrument_id:
            return self._reject(intent, "instrument_mismatch")
        if not self._is_step_aligned(intent.quantity, basis.quantity_step):
            return self._reject(intent, "quantity_rounding_invalid")
        if intent.quantity < basis.min_quantity:
            return self._reject(intent, "below_min_qty")
        if intent.order_type not in basis.supported_order_types:
            return self._reject(intent, "order_type_not_supported")
        if intent.time_in_force not in basis.supported_time_in_force:
            return self._reject(intent, "time_in_force_not_supported")
        if intent.order_type is OrderType.LIMIT:
            if intent.limit_price is None:
                return self._reject(intent, "missing_limit_price")
            if not self._is_step_aligned(intent.limit_price, basis.price_step):
                return self._reject(intent, "price_rounding_invalid")
            reference_price = intent.limit_price
        else:
            reference_price = basis.reference_price

        notional = intent.quantity * reference_price
        if notional < basis.min_notional:
            return self._reject(intent, "below_min_notional")

        return GuardOutcome.create(
            verdict=GuardVerdict.PASSED,
            order_intent_id=intent.order_intent_id,
            metadata={"instrument_id": basis.instrument_id},
        )

    def _reject(self, intent: OrderIntent, reason: str) -> GuardOutcome:
        return GuardOutcome.create(
            verdict=GuardVerdict.REJECTED,
            order_intent_id=intent.order_intent_id,
            reason=reason,
            metadata={"instrument_id": intent.instrument.instrument_id},
        )

    def _is_step_aligned(self, value: Decimal, step: Decimal) -> bool:
        return value % step == Decimal("0")

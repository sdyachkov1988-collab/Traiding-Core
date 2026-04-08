"""Startup-only reconciliation implementation for G2."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.reconciliation import (
    ExternalStartupBasis,
    ExternalStartupOrderRecord,
    StartupReconciliationResult,
    StartupReconciliationVerdict,
)
from trading_core.domain.state import PersistedOrderRecord
from trading_core.domain.state import PersistedStateSnapshot


@dataclass(slots=True)
class SimpleStartupReconciler:
    """Perform startup-only comparison between local and external state."""

    # `0` means exact Decimal equality is required. Any non-zero tolerance must
    # be chosen explicitly by the caller; there is no implicit fuzzy matching.
    cash_tolerance: Decimal = Decimal("0")
    quantity_tolerance: Decimal = Decimal("0")

    def reconcile(
        self,
        local_snapshot: PersistedStateSnapshot | None,
        external_basis: ExternalStartupBasis,
    ) -> StartupReconciliationResult:
        """Return a formal startup reconciliation result only."""

        if local_snapshot is None:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.INSUFFICIENT_DATA_OR_TIMEOUT,
                reason="no_local_snapshot",
            )

        local_portfolio = local_snapshot.portfolio_state
        cash_delta = abs(local_portfolio.cash_balance - external_basis.cash_balance)
        if cash_delta > self.cash_tolerance:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason="cash_balance_mismatch",
            )
        if local_portfolio.available_cash_balance != external_basis.available_cash_balance:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason="available_cash_balance_mismatch",
            )
        if local_portfolio.reserved_cash_balance != external_basis.reserved_cash_balance:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason="reserved_cash_balance_mismatch",
            )
        if local_portfolio.realized_pnl != external_basis.realized_pnl:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason="realized_pnl_mismatch",
            )
        if local_portfolio.equity != external_basis.equity:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason="equity_mismatch",
            )

        orders_match, order_reason = self._order_pictures_match(
            local_snapshot.order_picture,
            external_basis.order_picture,
        )
        if not orders_match:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason=order_reason,
            )

        local_instruments = set(local_portfolio.positions)
        external_instruments = set(external_basis.positions)
        if local_instruments != external_instruments:
            extra_local_instruments = local_instruments - external_instruments
            remaining_local_positions = local_portfolio.positions
            if extra_local_instruments and all(
                local_portfolio.positions[instrument_id].quantity == Decimal("0")
                for instrument_id in extra_local_instruments
            ):
                remaining_local_positions = {
                    instrument_id: position
                    for instrument_id, position in local_portfolio.positions.items()
                    if instrument_id not in extra_local_instruments
                }
                if set(remaining_local_positions) == external_instruments:
                    for instrument_id, local_position in remaining_local_positions.items():
                        external_position = external_basis.positions[instrument_id]
                        quantity_delta = abs(local_position.quantity - external_position.quantity)
                        if quantity_delta > self.quantity_tolerance:
                            return StartupReconciliationResult.create(
                                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                                reason="position_quantity_mismatch",
                                metadata={"instrument_id": instrument_id},
                            )
                    return StartupReconciliationResult.create(
                        verdict=StartupReconciliationVerdict.CORRECTED,
                        reason="zero_quantity_positions_pruned",
                        metadata={"instrument_ids": ",".join(sorted(extra_local_instruments))},
                    )
            if not local_instruments and not external_instruments:
                return StartupReconciliationResult.create(
                    verdict=StartupReconciliationVerdict.CORRECTED,
                    reason="position_picture_normalized",
                )
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                reason="position_set_mismatch",
            )

        for instrument_id, local_position in local_portfolio.positions.items():
            external_position = external_basis.positions[instrument_id]
            quantity_delta = abs(local_position.quantity - external_position.quantity)
            if quantity_delta > self.quantity_tolerance:
                return StartupReconciliationResult.create(
                    verdict=StartupReconciliationVerdict.CANNOT_RECONCILE,
                    reason="position_quantity_mismatch",
                    metadata={"instrument_id": instrument_id},
                )

        return StartupReconciliationResult.create(
            verdict=StartupReconciliationVerdict.CONSISTENT,
        )

    def _order_pictures_match(
        self,
        local_order_picture: dict[str, PersistedOrderRecord],
        external_order_picture: dict[str, ExternalStartupOrderRecord],
    ) -> tuple[bool, str | None]:
        if set(local_order_picture) != set(external_order_picture):
            return False, "order_picture_mismatch"

        for order_intent_id, local_record in local_order_picture.items():
            external_record = external_order_picture[order_intent_id]
            if local_record.external_order_id != external_record.external_order_id:
                return False, "order_picture_mismatch"
            if local_record.last_report_kind != external_record.last_report_kind:
                return False, "order_picture_mismatch"
            if local_record.reason != external_record.reason:
                return False, "order_picture_mismatch"

        return True, None

"""Startup-only reconciliation implementation for G2."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.reconciliation import (
    ExternalStartupBasis,
    StartupReconciliationResult,
    StartupReconciliationVerdict,
)
from trading_core.domain.state import PersistedStateSnapshot


@dataclass(slots=True)
class SimpleStartupReconciler:
    """Perform startup-only comparison between local and external state."""

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
                verdict=StartupReconciliationVerdict.LOCAL_STATE_MISSING,
                reason="no_local_snapshot",
            )

        local_portfolio = local_snapshot.portfolio_state
        cash_delta = abs(local_portfolio.cash_balance - external_basis.cash_balance)
        if cash_delta > self.cash_tolerance:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.MISMATCHED,
                reason="cash_balance_mismatch",
            )

        local_instruments = set(local_portfolio.positions)
        external_instruments = set(external_basis.positions)
        if local_instruments != external_instruments:
            return StartupReconciliationResult.create(
                verdict=StartupReconciliationVerdict.MISMATCHED,
                reason="position_set_mismatch",
            )

        for instrument_id, local_position in local_portfolio.positions.items():
            external_position = external_basis.positions[instrument_id]
            quantity_delta = abs(local_position.quantity - external_position.quantity)
            if quantity_delta > self.quantity_tolerance:
                return StartupReconciliationResult.create(
                    verdict=StartupReconciliationVerdict.MISMATCHED,
                    reason="position_quantity_mismatch",
                    metadata={"instrument_id": instrument_id},
                )

        return StartupReconciliationResult.create(
            verdict=StartupReconciliationVerdict.MATCHED,
        )

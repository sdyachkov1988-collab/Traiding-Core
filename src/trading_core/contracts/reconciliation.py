"""Contracts for G2 startup reconciliation."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.reconciliation import ExternalStartupBasis, StartupReconciliationResult
from trading_core.domain.state import PersistedStateSnapshot


class StartupReconciler(Protocol):
    """Compare local restored state with external startup basis."""

    def reconcile(
        self,
        local_snapshot: PersistedStateSnapshot | None,
        external_basis: ExternalStartupBasis,
    ) -> StartupReconciliationResult:
        """Return only the formal startup reconciliation result."""

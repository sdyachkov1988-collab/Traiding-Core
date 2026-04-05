"""Contracts for D2 pre-execution guard seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.guards import ExecutionAdmissibilityBasis, GuardOutcome
from trading_core.domain.orders import OrderIntent


class PreExecutionGuard(Protocol):
    """Validate that an order intent is still formally admissible."""

    def check(
        self,
        intent: OrderIntent,
        basis: ExecutionAdmissibilityBasis,
    ) -> GuardOutcome:
        """Return only the guard outcome, without exiting to execution."""

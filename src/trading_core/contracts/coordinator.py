"""Contracts for the Wave 2D Recovery Coordinator."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.reconciliation_extended import ReconciliationOutcome, ReconciliationRequest
from trading_core.domain.unknown import SystemModeTransition


class RecoveryCoordinatorProtocol(Protocol):
    """Coordinate reconciliation requests and failure-path transitions."""

    def request_startup_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest: ...

    def request_periodic_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest: ...

    def request_on_error_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest: ...

    def process_outcome(self, outcome: ReconciliationOutcome) -> SystemModeTransition | None: ...

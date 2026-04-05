"""Recovery Coordinator for Wave 2D reconciliation modes."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.domain.reconciliation_extended import (
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationRequest,
    ReconciliationTrigger,
)
from trading_core.domain.unknown import SystemModeTransition
from trading_core.reconciliation.source_of_truth import SourceOfTruthPolicy
from trading_core.recovery.classifier import UnknownStateClassifier


@dataclass(slots=True)
class RecoveryCoordinator:
    """Coordinate startup, periodic, and on-error reconciliation requests."""

    source_of_truth: SourceOfTruthPolicy
    classifier: UnknownStateClassifier

    def request_startup_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Create a startup reconciliation request."""

        return ReconciliationRequest.create(
            mode=ReconciliationMode.STARTUP,
            trigger=ReconciliationTrigger.SYSTEM_START,
            instrument_id=instrument_id,
        )

    def request_periodic_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Create a periodic reconciliation request."""

        return ReconciliationRequest.create(
            mode=ReconciliationMode.PERIODIC,
            trigger=ReconciliationTrigger.SCHEDULER,
            instrument_id=instrument_id,
        )

    def request_on_error_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Create an on-error reconciliation request."""

        return ReconciliationRequest.create(
            mode=ReconciliationMode.ON_ERROR,
            trigger=ReconciliationTrigger.ERROR_SIGNAL,
            instrument_id=instrument_id,
        )

    def process_outcome(
        self,
        outcome: ReconciliationOutcome,
    ) -> SystemModeTransition | None:
        """Convert conflicting reconciliation results into safe-mode transitions."""

        if outcome.conflicts_with_active_trading is False:
            return None

        _record, transition = self.classifier.classify_unknown_position(
            instrument_id=outcome.instrument_id or "unknown",
            reason=outcome.reason or "reconciliation_conflict_with_active_trading",
        )
        return transition

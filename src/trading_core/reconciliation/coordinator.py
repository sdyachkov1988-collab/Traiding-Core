"""Recovery Coordinator for Wave 2D reconciliation modes."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.domain.reconciliation_extended import (
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationRequest,
    ReconciliationTrigger,
    ReconciliationVerdict,
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
        """Convert unresolved reconciliation results into formal safety-path transitions."""

        if outcome.allows_normal_continuation():
            return None

        if outcome.verdict is ReconciliationVerdict.INSUFFICIENT:
            _record, transition = self.classifier.classify_insufficient_reconciliation(
                request_id=outcome.request_id,
                instrument_id=outcome.instrument_id,
                reason=outcome.reason or "reconciliation_basis_insufficient",
                to_mode=self.source_of_truth.mode_for_insufficient_basis(),
            )
            self.classifier.apply_transition(transition)
            return transition

        if outcome.verdict is not ReconciliationVerdict.CONFLICTING:
            return None

        conflict_mode = self.source_of_truth.mode_for_position_conflict(
            conflicts_with_active_trading=outcome.conflicts_with_active_trading,
        )
        _record, transition = self.classifier.classify_conflicting_reconciliation(
            request_id=outcome.request_id,
            instrument_id=outcome.instrument_id,
            reason=outcome.reason or "reconciliation_conflict_with_active_trading",
            to_mode=conflict_mode,
        )
        self.classifier.apply_transition(transition)
        return transition

from __future__ import annotations

from datetime import datetime, timezone

from dataclasses import dataclass

from trading_core.domain import (
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationRequest,
    ReconciliationTrigger,
    ReconciliationVerdict,
    SystemMode,
    UnknownStateKind,
)
from trading_core.reconciliation import RecoveryCoordinator, SourceOfTruthPolicy
from trading_core.recovery import UnknownStateClassifier


def test_reconciliation_request_create_builds_startup_request() -> None:
    request = ReconciliationRequest.create(
        mode=ReconciliationMode.STARTUP,
        trigger=ReconciliationTrigger.SYSTEM_START,
        instrument_id="btc-usdt",
    )

    assert request.request_id.startswith("recon_req_")
    assert request.mode == ReconciliationMode.STARTUP
    assert request.trigger == ReconciliationTrigger.SYSTEM_START
    assert request.requested_at.tzinfo == timezone.utc


def test_reconciliation_request_create_builds_periodic_request() -> None:
    request = ReconciliationRequest.create(
        mode=ReconciliationMode.PERIODIC,
        trigger=ReconciliationTrigger.SCHEDULER,
    )

    assert request.mode == ReconciliationMode.PERIODIC
    assert request.trigger == ReconciliationTrigger.SCHEDULER


def test_reconciliation_request_create_builds_on_error_request() -> None:
    request = ReconciliationRequest.create(
        mode=ReconciliationMode.ON_ERROR,
        trigger=ReconciliationTrigger.ERROR_SIGNAL,
    )

    assert request.mode == ReconciliationMode.ON_ERROR
    assert request.trigger == ReconciliationTrigger.ERROR_SIGNAL


def test_reconciliation_outcome_create_preserves_conflict_flag() -> None:
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CONFLICTING,
        conflicts_with_active_trading=True,
        reason="position_conflict",
    )

    assert outcome.outcome_id.startswith("recon_out_")
    assert outcome.conflicts_with_active_trading is True
    assert outcome.resolved_at.tzinfo == timezone.utc


def test_recovery_coordinator_creates_startup_request() -> None:
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=UnknownStateClassifier(),
    )

    request = coordinator.request_startup_reconciliation("btc-usdt")

    assert request.mode == ReconciliationMode.STARTUP
    assert request.trigger == ReconciliationTrigger.SYSTEM_START


def test_recovery_coordinator_creates_periodic_request() -> None:
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=UnknownStateClassifier(),
    )

    request = coordinator.request_periodic_reconciliation("btc-usdt")

    assert request.mode == ReconciliationMode.PERIODIC
    assert request.trigger == ReconciliationTrigger.SCHEDULER


def test_recovery_coordinator_creates_on_error_request() -> None:
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=UnknownStateClassifier(),
    )

    request = coordinator.request_on_error_reconciliation("btc-usdt")

    assert request.mode == ReconciliationMode.ON_ERROR
    assert request.trigger == ReconciliationTrigger.ERROR_SIGNAL


def test_recovery_coordinator_process_outcome_with_conflict_returns_safe_mode_transition() -> None:
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=UnknownStateClassifier(),
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CONFLICTING,
        conflicts_with_active_trading=True,
        reason="position_conflict",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.SAFE_MODE


@dataclass
class ProtocolOnlyClassifier:
    current_mode: SystemMode = SystemMode.NORMAL

    def classify_missing_execution_confirmation(self, order_intent_id: str, instrument_id: str):
        raise NotImplementedError

    def classify_unknown_position(self, instrument_id: str, reason: str):
        raise NotImplementedError

    def classify_stale_context(self, instrument_id: str):
        raise NotImplementedError

    def classify_unknown_order_state(self, order_intent_id: str, instrument_id: str, reason: str):
        raise NotImplementedError

    def classify_insufficient_reconciliation(self, *, request_id: str, instrument_id: str | None, reason: str, to_mode: object):
        return UnknownStateClassifier(self.current_mode).classify_insufficient_reconciliation(
            request_id=request_id,
            instrument_id=instrument_id,
            reason=reason,
            to_mode=to_mode,
        )

    def classify_conflicting_reconciliation(self, *, request_id: str, instrument_id: str | None, reason: str, to_mode: object):
        return UnknownStateClassifier(self.current_mode).classify_conflicting_reconciliation(
            request_id=request_id,
            instrument_id=instrument_id,
            reason=reason,
            to_mode=to_mode,
        )

    def is_trading_allowed(self) -> bool:
        return self.current_mode is SystemMode.NORMAL

    def apply_transition(self, transition):
        self.current_mode = transition.to_mode


def test_recovery_coordinator_process_outcome_with_conflict_blocks_trading() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CONFLICTING,
        conflicts_with_active_trading=True,
        reason="position_conflict",
        instrument_id="btc-usdt",
    )

    coordinator.process_outcome(outcome)

    assert classifier.current_mode != SystemMode.NORMAL
    assert classifier.is_trading_allowed() is False


def test_recovery_coordinator_applies_returned_transition_to_classifier_mode() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CONFLICTING,
        conflicts_with_active_trading=True,
        reason="position_conflict",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert classifier.current_mode == transition.to_mode
    assert classifier.current_mode == SystemMode.SAFE_MODE


def test_recovery_coordinator_process_outcome_without_conflict_returns_none() -> None:
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=UnknownStateClassifier(),
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.ALIGNED,
        conflicts_with_active_trading=False,
    )

    assert coordinator.process_outcome(outcome) is None


def test_recovery_coordinator_treats_corrected_outcome_as_formal_non_blocking_result() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CORRECTED,
        conflicts_with_active_trading=False,
        reason="local_picture_corrected_from_external_truth",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is None
    assert outcome.allows_normal_continuation() is True
    assert outcome.is_conflict_bearing() is False
    assert classifier.current_mode == SystemMode.NORMAL


def test_recovery_coordinator_blocks_insufficient_outcome_via_read_only_path() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.ON_ERROR,
        verdict=ReconciliationVerdict.INSUFFICIENT,
        conflicts_with_active_trading=False,
        reason="external_basis_insufficient",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.READ_ONLY
    assert classifier.current_mode == SystemMode.READ_ONLY
    assert classifier.is_trading_allowed() is False
    assert outcome.allows_normal_continuation() is False
    assert outcome.is_conflict_bearing() is True
    assert transition.unknown_state is not None
    assert transition.unknown_state.kind == UnknownStateKind.RECONCILIATION_INSUFFICIENT
    assert transition.unknown_state.reason == "external_basis_insufficient"


def test_recovery_coordinator_works_against_protocol_declared_surface() -> None:
    classifier = ProtocolOnlyClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.ON_ERROR,
        verdict=ReconciliationVerdict.INSUFFICIENT,
        conflicts_with_active_trading=False,
        reason="external_basis_insufficient",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert classifier.current_mode == SystemMode.READ_ONLY


def test_recovery_coordinator_does_not_use_request_id_as_order_intent_id_for_insufficient_outcome() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.ON_ERROR,
        verdict=ReconciliationVerdict.INSUFFICIENT,
        conflicts_with_active_trading=False,
        reason="external_basis_insufficient",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.unknown_state is not None
    assert transition.unknown_state.order_intent_id is None
    assert transition.unknown_state.metadata["reconciliation_request_id"] == "recon_req_123"


def test_recovery_coordinator_returns_explicit_path_for_non_active_conflict() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CONFLICTING,
        conflicts_with_active_trading=False,
        reason="position_conflict_detected",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.READ_ONLY
    assert transition.unknown_state is not None
    assert transition.unknown_state.kind == UnknownStateKind.RECONCILIATION_CONFLICT
    assert classifier.current_mode == SystemMode.READ_ONLY
    assert classifier.is_trading_allowed() is False


def test_source_of_truth_policy_operationally_controls_conflict_mode() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(non_active_conflict_mode=SystemMode.SAFE_MODE),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.CONFLICTING,
        conflicts_with_active_trading=False,
        reason="position_conflict_detected",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.SAFE_MODE
    assert classifier.current_mode == SystemMode.SAFE_MODE


def test_recovery_coordinator_does_not_downgrade_existing_safe_mode_on_weaker_outcome() -> None:
    classifier = UnknownStateClassifier(current_mode=SystemMode.SAFE_MODE)
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.ON_ERROR,
        verdict=ReconciliationVerdict.INSUFFICIENT,
        conflicts_with_active_trading=False,
        reason="external_basis_insufficient",
        instrument_id="btc-usdt",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.READ_ONLY
    assert classifier.current_mode == SystemMode.SAFE_MODE


def test_source_of_truth_policy_blocks_trading_on_position_conflict() -> None:
    policy = SourceOfTruthPolicy()

    assert policy.blocks_trading_on_position_conflict() is True


def test_source_of_truth_policy_exposes_explicit_authorities_and_layers() -> None:
    policy = SourceOfTruthPolicy()

    assert policy.authoritative_source_for_execution_facts() == "external_venue"
    assert policy.authoritative_source_for_market_data() == "canonical_instrument_scoped_data_layer"
    assert (
        policy.authoritative_source_for_position_truth()
        == "external_execution_state_via_reconciliation"
    )
    assert policy.local_picture_class == "local_observed_state"
    assert policy.external_picture_class == "external_observed_state"
    assert policy.derived_state_class == "derived_internal_state"
    assert policy.reconciled_truth_class == "reconciliation_outcome_layer"
    assert policy.reconciliation_outcome_is_distinct_from_observed_pictures() is True
    assert policy.mode_for_insufficient_basis() == SystemMode.READ_ONLY
    assert policy.mode_for_position_conflict(conflicts_with_active_trading=False) == SystemMode.READ_ONLY
    assert policy.mode_for_position_conflict(conflicts_with_active_trading=True) == SystemMode.SAFE_MODE


def test_reconciliation_mode_has_three_expected_values() -> None:
    assert ReconciliationMode.STARTUP.value == "startup"
    assert ReconciliationMode.PERIODIC.value == "periodic"
    assert ReconciliationMode.ON_ERROR.value == "on_error"


def test_reconciliation_verdict_excludes_startup_only_local_state_missing() -> None:
    assert ReconciliationVerdict.ALIGNED.value == "aligned"
    assert ReconciliationVerdict.CORRECTED.value == "corrected"
    assert ReconciliationVerdict.INSUFFICIENT.value == "insufficient"
    assert ReconciliationVerdict.CONFLICTING.value == "conflicting"
    assert "local_state_missing" not in {verdict.value for verdict in ReconciliationVerdict}


def test_reconciliation_outcome_rejects_naive_resolved_at_datetime() -> None:
    try:
        ReconciliationOutcome(
            outcome_id="recon_out_123",
            request_id="recon_req_123",
            mode=ReconciliationMode.PERIODIC,
            verdict=ReconciliationVerdict.ALIGNED,
            instrument_id="btc-usdt",
            conflicts_with_active_trading=False,
            reason=None,
            resolved_at=datetime(2026, 1, 1, 12, 0, 0),
        )
    except ValueError as exc:
        assert str(exc) == "resolved_at must be timezone-aware UTC"
    else:
        raise AssertionError("Expected naive resolved_at to be rejected")


def test_reconciliation_trigger_has_four_expected_values() -> None:
    assert ReconciliationTrigger.SYSTEM_START.value == "system_start"
    assert ReconciliationTrigger.SCHEDULER.value == "scheduler"
    assert ReconciliationTrigger.ERROR_SIGNAL.value == "error_signal"
    assert ReconciliationTrigger.OPERATOR_COMMAND.value == "operator_command"

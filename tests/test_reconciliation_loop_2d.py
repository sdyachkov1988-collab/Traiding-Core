from __future__ import annotations

from datetime import datetime, timezone

from trading_core.domain import (
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationRequest,
    ReconciliationTrigger,
    ReconciliationVerdict,
    SystemMode,
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
        verdict=ReconciliationVerdict.MISMATCHED,
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
        verdict=ReconciliationVerdict.MISMATCHED,
        conflicts_with_active_trading=True,
        reason="position_conflict",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.SAFE_MODE


def test_recovery_coordinator_process_outcome_with_conflict_blocks_trading() -> None:
    classifier = UnknownStateClassifier()
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=classifier,
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=ReconciliationVerdict.MISMATCHED,
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
        verdict=ReconciliationVerdict.MISMATCHED,
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
        verdict=ReconciliationVerdict.MATCHED,
        conflicts_with_active_trading=False,
    )

    assert coordinator.process_outcome(outcome) is None


def test_source_of_truth_policy_blocks_trading_on_position_conflict() -> None:
    policy = SourceOfTruthPolicy()

    assert policy.blocks_trading_on_position_conflict() is True


def test_reconciliation_mode_has_three_expected_values() -> None:
    assert ReconciliationMode.STARTUP.value == "startup"
    assert ReconciliationMode.PERIODIC.value == "periodic"
    assert ReconciliationMode.ON_ERROR.value == "on_error"


def test_reconciliation_verdict_excludes_startup_only_local_state_missing() -> None:
    assert ReconciliationVerdict.MATCHED.value == "matched"
    assert ReconciliationVerdict.MISMATCHED.value == "mismatched"
    assert "local_state_missing" not in {verdict.value for verdict in ReconciliationVerdict}


def test_reconciliation_outcome_rejects_naive_resolved_at_datetime() -> None:
    try:
        ReconciliationOutcome(
            outcome_id="recon_out_123",
            request_id="recon_req_123",
            mode=ReconciliationMode.PERIODIC,
            verdict=ReconciliationVerdict.MATCHED,
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

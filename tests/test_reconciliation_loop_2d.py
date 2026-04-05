from __future__ import annotations

from datetime import timezone

from trading_core.domain import (
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationRequest,
    ReconciliationTrigger,
    StartupReconciliationVerdict,
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
        verdict=StartupReconciliationVerdict.MISMATCHED,
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
        verdict=StartupReconciliationVerdict.MISMATCHED,
        conflicts_with_active_trading=True,
        reason="position_conflict",
    )

    transition = coordinator.process_outcome(outcome)

    assert transition is not None
    assert transition.to_mode == SystemMode.SAFE_MODE


def test_recovery_coordinator_process_outcome_without_conflict_returns_none() -> None:
    coordinator = RecoveryCoordinator(
        source_of_truth=SourceOfTruthPolicy(),
        classifier=UnknownStateClassifier(),
    )
    outcome = ReconciliationOutcome.create(
        request_id="recon_req_123",
        mode=ReconciliationMode.PERIODIC,
        verdict=StartupReconciliationVerdict.MATCHED,
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


def test_reconciliation_trigger_has_four_expected_values() -> None:
    assert ReconciliationTrigger.SYSTEM_START.value == "system_start"
    assert ReconciliationTrigger.SCHEDULER.value == "scheduler"
    assert ReconciliationTrigger.ERROR_SIGNAL.value == "error_signal"
    assert ReconciliationTrigger.OPERATOR_COMMAND.value == "operator_command"

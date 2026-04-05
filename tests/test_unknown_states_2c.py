from __future__ import annotations

from datetime import timezone

from trading_core.domain import (
    SystemMode,
    SystemModeTransition,
    UnknownStateKind,
    UnknownStateRecord,
)
from trading_core.recovery import UnknownStateClassifier


def test_unknown_state_record_create_builds_valid_unknown_order_state() -> None:
    record = UnknownStateRecord.create(
        kind=UnknownStateKind.UNKNOWN_ORDER_STATE,
        reason="order_status_missing",
        instrument_id="btc-usdt",
        order_intent_id="ordint_123",
    )

    assert record.record_id.startswith("unknown_")
    assert record.kind == UnknownStateKind.UNKNOWN_ORDER_STATE
    assert record.detected_at.tzinfo == timezone.utc


def test_system_mode_transition_create_tracks_normal_to_read_only() -> None:
    transition = SystemModeTransition.create(
        from_mode=SystemMode.NORMAL,
        to_mode=SystemMode.READ_ONLY,
        reason="missing_execution_confirmation",
    )

    assert transition.from_mode == SystemMode.NORMAL
    assert transition.to_mode == SystemMode.READ_ONLY
    assert transition.reason == "missing_execution_confirmation"
    assert transition.transitioned_at.tzinfo == timezone.utc


def test_classifier_marks_missing_execution_confirmation_as_read_only() -> None:
    classifier = UnknownStateClassifier()

    record, transition = classifier.classify_missing_execution_confirmation(
        order_intent_id="ordint_123",
        instrument_id="btc-usdt",
    )

    assert record.kind == UnknownStateKind.INCOMPLETE_EXTERNAL_CONFIRMATION
    assert transition.to_mode == SystemMode.READ_ONLY


def test_classifier_marks_unknown_position_as_safe_mode() -> None:
    classifier = UnknownStateClassifier()

    record, transition = classifier.classify_unknown_position(
        instrument_id="btc-usdt",
        reason="position_reality_uncertain",
    )

    assert record.kind == UnknownStateKind.UNKNOWN_POSITION_STATE
    assert transition.to_mode == SystemMode.SAFE_MODE


def test_classifier_marks_stale_context_as_read_only() -> None:
    classifier = UnknownStateClassifier()

    record, transition = classifier.classify_stale_context("btc-usdt")

    assert record.kind == UnknownStateKind.STALE_CONTEXT
    assert transition.to_mode == SystemMode.READ_ONLY


def test_classifier_marks_unknown_order_state_as_read_only() -> None:
    classifier = UnknownStateClassifier()

    record, transition = classifier.classify_unknown_order_state(
        order_intent_id="ordint_123",
        instrument_id="btc-usdt",
        reason="order_state_conflict",
    )

    assert record.kind == UnknownStateKind.UNKNOWN_ORDER_STATE
    assert transition.to_mode == SystemMode.READ_ONLY


def test_is_trading_allowed_only_in_normal_mode() -> None:
    classifier = UnknownStateClassifier()

    assert classifier.is_trading_allowed() is True
    classifier.current_mode = SystemMode.READ_ONLY
    assert classifier.is_trading_allowed() is False
    classifier.current_mode = SystemMode.SAFE_MODE
    assert classifier.is_trading_allowed() is False


def test_apply_transition_changes_current_mode() -> None:
    classifier = UnknownStateClassifier()
    transition = SystemModeTransition.create(
        from_mode=SystemMode.NORMAL,
        to_mode=SystemMode.READ_ONLY,
        reason="missing_execution_confirmation",
    )

    classifier.apply_transition(transition)

    assert classifier.current_mode == SystemMode.READ_ONLY


def test_unknown_position_transition_blocks_trading_after_apply() -> None:
    classifier = UnknownStateClassifier()
    _record, transition = classifier.classify_unknown_position(
        instrument_id="btc-usdt",
        reason="position_reality_uncertain",
    )

    classifier.apply_transition(transition)

    assert classifier.is_trading_allowed() is False


def test_system_mode_and_unknown_state_kind_values_are_correct() -> None:
    assert SystemMode.NORMAL.value == "normal"
    assert SystemMode.READ_ONLY.value == "read_only"
    assert SystemMode.SAFE_MODE.value == "safe_mode"
    assert SystemMode.FROZEN.value == "frozen"
    assert UnknownStateKind.UNKNOWN_ORDER_STATE.value == "unknown_order_state"
    assert UnknownStateKind.UNKNOWN_POSITION_STATE.value == "unknown_position_state"
    assert UnknownStateKind.STALE_CONTEXT.value == "stale_context"
    assert (
        UnknownStateKind.INCOMPLETE_EXTERNAL_CONFIRMATION.value
        == "incomplete_external_confirmation"
    )

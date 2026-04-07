"""Unknown-state classifier and system-mode transitions for Wave 2C."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.domain.unknown import (
    SystemMode,
    SystemModeTransition,
    UnknownStateKind,
    UnknownStateRecord,
)


def _mode_rank(mode: SystemMode) -> int:
    if mode is SystemMode.NORMAL:
        return 0
    if mode is SystemMode.READ_ONLY:
        return 1
    if mode is SystemMode.SAFE_MODE:
        return 2
    return 3


@dataclass(slots=True)
class UnknownStateClassifier:
    """Classify unknown states and map them into formal system modes."""

    current_mode: SystemMode = SystemMode.NORMAL

    def classify_missing_execution_confirmation(
        self,
        order_intent_id: str,
        instrument_id: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]:
        """Classify a missing execution confirmation as a read-only failure path."""

        record = UnknownStateRecord.create(
            kind=UnknownStateKind.INCOMPLETE_EXTERNAL_CONFIRMATION,
            reason="missing_execution_confirmation",
            instrument_id=instrument_id,
            order_intent_id=order_intent_id,
        )
        transition = SystemModeTransition.create(
            from_mode=self.current_mode,
            to_mode=SystemMode.READ_ONLY,
            reason="missing_execution_confirmation",
            unknown_state=record,
        )
        return record, transition

    def classify_unknown_position(
        self,
        instrument_id: str,
        reason: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]:
        """Classify an unknown position as a safe-mode failure path."""

        record = UnknownStateRecord.create(
            kind=UnknownStateKind.UNKNOWN_POSITION_STATE,
            reason=reason,
            instrument_id=instrument_id,
        )
        transition = SystemModeTransition.create(
            from_mode=self.current_mode,
            to_mode=SystemMode.SAFE_MODE,
            reason=reason,
            unknown_state=record,
        )
        return record, transition

    def classify_stale_context(
        self,
        instrument_id: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]:
        """Classify a stale context as a read-only failure path."""

        record = UnknownStateRecord.create(
            kind=UnknownStateKind.STALE_CONTEXT,
            reason="stale_context",
            instrument_id=instrument_id,
        )
        transition = SystemModeTransition.create(
            from_mode=self.current_mode,
            to_mode=SystemMode.READ_ONLY,
            reason="stale_context",
            unknown_state=record,
        )
        return record, transition

    def classify_unknown_order_state(
        self,
        order_intent_id: str,
        instrument_id: str,
        reason: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]:
        """Classify an unknown order state as a read-only failure path."""

        record = UnknownStateRecord.create(
            kind=UnknownStateKind.UNKNOWN_ORDER_STATE,
            reason=reason,
            instrument_id=instrument_id,
            order_intent_id=order_intent_id,
        )
        transition = SystemModeTransition.create(
            from_mode=self.current_mode,
            to_mode=SystemMode.READ_ONLY,
            reason=reason,
            unknown_state=record,
        )
        return record, transition

    def classify_insufficient_reconciliation(
        self,
        *,
        request_id: str,
        instrument_id: str | None,
        reason: str,
        to_mode: SystemMode = SystemMode.READ_ONLY,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]:
        """Classify unresolved reconciliation basis without collapsing it into execution-only meaning."""

        record = UnknownStateRecord.create(
            kind=UnknownStateKind.RECONCILIATION_INSUFFICIENT,
            reason=reason,
            instrument_id=instrument_id,
            metadata={"reconciliation_request_id": request_id},
        )
        transition = SystemModeTransition.create(
            from_mode=self.current_mode,
            to_mode=to_mode,
            reason=reason,
            unknown_state=record,
        )
        return record, transition

    def classify_conflicting_reconciliation(
        self,
        *,
        request_id: str,
        instrument_id: str | None,
        reason: str,
        to_mode: SystemMode,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]:
        """Classify reconciliation conflict without masking it as a narrower unknown-state class."""

        record = UnknownStateRecord.create(
            kind=UnknownStateKind.RECONCILIATION_CONFLICT,
            reason=reason,
            instrument_id=instrument_id,
            metadata={"reconciliation_request_id": request_id},
        )
        transition = SystemModeTransition.create(
            from_mode=self.current_mode,
            to_mode=to_mode,
            reason=reason,
            unknown_state=record,
        )
        return record, transition

    def is_trading_allowed(self) -> bool:
        """Trading is allowed only while the system stays in NORMAL mode."""

        return self.current_mode is SystemMode.NORMAL

    def apply_transition(self, transition: SystemModeTransition) -> None:
        """Apply a mode transition produced by the classifier."""

        if _mode_rank(transition.to_mode) < _mode_rank(self.current_mode):
            return
        self.current_mode = transition.to_mode

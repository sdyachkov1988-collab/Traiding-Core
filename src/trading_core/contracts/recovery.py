"""Contracts for Wave 2C unknown-state classification."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from trading_core.domain.unknown import SystemModeTransition, UnknownStateRecord


@runtime_checkable
class UnknownStateClassifierProtocol(Protocol):
    """Classify unknown states and expose trading-admission posture."""

    def classify_missing_execution_confirmation(
        self,
        order_intent_id: str,
        instrument_id: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]: ...

    def classify_unknown_position(
        self,
        instrument_id: str,
        reason: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]: ...

    def classify_stale_context(
        self,
        instrument_id: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]: ...

    def classify_unknown_order_state(
        self,
        order_intent_id: str,
        instrument_id: str,
        reason: str,
    ) -> tuple[UnknownStateRecord, SystemModeTransition]: ...

    def is_trading_allowed(self) -> bool: ...

    def apply_transition(self, transition: SystemModeTransition) -> None: ...

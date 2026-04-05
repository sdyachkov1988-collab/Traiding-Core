"""Extended reconciliation domain objects for Wave 2D."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now


class ReconciliationMode(StrEnum):
    """Operational reconciliation modes for the normal loop."""

    STARTUP = "startup"
    PERIODIC = "periodic"
    ON_ERROR = "on_error"


class ReconciliationTrigger(StrEnum):
    """Triggers that request reconciliation from the coordinator."""

    SYSTEM_START = "system_start"
    SCHEDULER = "scheduler"
    ERROR_SIGNAL = "error_signal"
    OPERATOR_COMMAND = "operator_command"


class ReconciliationVerdict(StrEnum):
    """Loop-level reconciliation verdict without startup-only missing-state semantics."""

    MATCHED = "matched"
    MISMATCHED = "mismatched"


@dataclass(frozen=True, slots=True)
class ReconciliationRequest:
    """Formal reconciliation request across startup, periodic, and on-error modes."""

    request_id: str
    mode: ReconciliationMode
    trigger: ReconciliationTrigger
    instrument_id: str | None
    requested_at: datetime

    def __post_init__(self) -> None:
        require_utc_datetime(self.requested_at, "requested_at")

    @classmethod
    def create(
        cls,
        *,
        mode: ReconciliationMode,
        trigger: ReconciliationTrigger,
        instrument_id: str | None = None,
    ) -> "ReconciliationRequest":
        """Build a reconciliation request with generated identity."""

        return cls(
            request_id=new_internal_id("recon_req"),
            mode=mode,
            trigger=trigger,
            instrument_id=instrument_id,
            requested_at=utc_now(),
        )


@dataclass(frozen=True, slots=True)
class ReconciliationOutcome:
    """Formal reconciliation outcome for the normal operating loop."""

    outcome_id: str
    request_id: str
    mode: ReconciliationMode
    verdict: ReconciliationVerdict
    instrument_id: str | None
    conflicts_with_active_trading: bool
    reason: str | None
    resolved_at: datetime

    def __post_init__(self) -> None:
        require_utc_datetime(self.resolved_at, "resolved_at")

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        mode: ReconciliationMode,
        verdict: ReconciliationVerdict,
        instrument_id: str | None = None,
        conflicts_with_active_trading: bool,
        reason: str | None = None,
    ) -> "ReconciliationOutcome":
        """Build a reconciliation outcome with generated identity."""

        return cls(
            outcome_id=new_internal_id("recon_out"),
            request_id=request_id,
            mode=mode,
            verdict=verdict,
            instrument_id=instrument_id,
            conflicts_with_active_trading=conflicts_with_active_trading,
            reason=reason,
            resolved_at=utc_now(),
        )

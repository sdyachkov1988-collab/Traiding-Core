"""Startup-only reconciliation models for G2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now


class StartupReconciliationVerdict(StrEnum):
    """Formal startup-only reconciliation verdict."""

    CONSISTENT = "consistent"
    CORRECTED = "corrected"
    CANNOT_RECONCILE = "cannot_reconcile"
    INSUFFICIENT_DATA_OR_TIMEOUT = "insufficient_data_or_timeout"


@dataclass(frozen=True, slots=True)
class ExternalStartupPosition:
    """Minimal external startup position view."""

    instrument_id: str
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class ExternalStartupBasis:
    """External startup view used only by startup reconciliation."""

    cash_balance: Decimal
    positions: Mapping[str, ExternalStartupPosition]
    observed_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.observed_at, "observed_at")

    @classmethod
    def create(
        cls,
        *,
        cash_balance: Decimal,
        positions: Mapping[str, ExternalStartupPosition] | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "ExternalStartupBasis":
        return cls(
            cash_balance=cash_balance,
            positions=dict(positions or {}),
            observed_at=utc_now(),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class StartupReconciliationResult:
    """Formal startup reconciliation result without governance semantics."""

    reconciliation_result_id: str
    verdict: StartupReconciliationVerdict
    checked_at: datetime
    reason: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.checked_at, "checked_at")

    @classmethod
    def create(
        cls,
        *,
        verdict: StartupReconciliationVerdict,
        reason: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "StartupReconciliationResult":
        return cls(
            reconciliation_result_id=new_internal_id("reconcile"),
            verdict=verdict,
            checked_at=utc_now(),
            reason=reason,
            metadata=dict(metadata or {}),
        )

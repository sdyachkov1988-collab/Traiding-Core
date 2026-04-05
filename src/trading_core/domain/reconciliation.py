"""Startup-only reconciliation models for G2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import new_internal_id, utc_now


class StartupReconciliationVerdict(StrEnum):
    """Formal startup-only reconciliation verdict."""

    MATCHED = "matched"
    MISMATCHED = "mismatched"
    LOCAL_STATE_MISSING = "local_state_missing"


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

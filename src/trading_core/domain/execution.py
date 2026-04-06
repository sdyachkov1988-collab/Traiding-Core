"""Execution-boundary domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now
from trading_core.domain.guards import GuardOutcome, GuardVerdict
from trading_core.domain.orders import OrderIntent


class ExecutionReportKind(StrEnum):
    """Normalized execution-side update kinds returned by the boundary."""

    SUBMITTED = "submitted"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACKNOWLEDGED = "acknowledged"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class AdmittedOrder:
    """Order admitted by D2 and allowed to cross the execution boundary."""

    admitted_order_id: str
    order_intent: OrderIntent
    guard_outcome: GuardOutcome
    admitted_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.admitted_at, "admitted_at")

    @classmethod
    def create(
        cls,
        *,
        order_intent: OrderIntent,
        guard_outcome: GuardOutcome,
        metadata: Mapping[str, str] | None = None,
    ) -> "AdmittedOrder":
        """Create an execution-ready order only from a passed guard outcome."""

        if guard_outcome.verdict is not GuardVerdict.PASSED:
            raise ValueError("AdmittedOrder requires a passed GuardOutcome")
        if guard_outcome.order_intent_id != order_intent.order_intent_id:
            raise ValueError("GuardOutcome does not match OrderIntent")

        return cls(
            admitted_order_id=new_internal_id("admitted"),
            order_intent=order_intent,
            guard_outcome=guard_outcome,
            admitted_at=utc_now(),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    """Normalized execution-side update/report returned by Package E."""

    report_id: str
    kind: ExecutionReportKind
    order_intent_id: str
    observed_at: datetime
    external_order_id: str | None = None
    reason: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.observed_at, "observed_at")

    @classmethod
    def create(
        cls,
        *,
        kind: ExecutionReportKind,
        order_intent_id: str,
        external_order_id: str | None = None,
        reason: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "ExecutionReport":
        """Create a normalized execution-side report."""

        return cls(
            report_id=new_internal_id("exec"),
            kind=kind,
            order_intent_id=order_intent_id,
            observed_at=utc_now(),
            external_order_id=external_order_id,
            reason=reason,
            metadata=dict(metadata or {}),
        )

"""Position-originated close-routing domain objects for Wave 2E."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from trading_core.domain.common import InstrumentRef, new_internal_id, require_utc_datetime, utc_now


class CloseRoutingVerdict(StrEnum):
    """Formal outcomes for the position-originated close-routing contour."""

    ADMITTED = "admitted"
    REJECTED = "rejected"
    GUARD_REJECTED = "guard_rejected"
    EXECUTION_REJECTED = "execution_rejected"
    RECONCILE_REQUIRED = "reconcile_required"
    SAFE_MODE_TRIGGERED = "safe_mode_triggered"


@dataclass(frozen=True, slots=True)
class CloseIntent:
    """Formal close intent emitted by the position-management layer."""

    intent_id: str
    instrument: InstrumentRef
    position_id: str
    quantity: Decimal
    reason: str
    created_at: datetime

    def __post_init__(self) -> None:
        require_utc_datetime(self.created_at, "created_at")
        if self.quantity <= Decimal("0"):
            raise ValueError("close_quantity_must_be_positive")
        if self.reason.strip() == "":
            raise ValueError("close_reason_must_not_be_blank")

    @classmethod
    def create(
        cls,
        *,
        instrument: InstrumentRef,
        position_id: str,
        quantity: Decimal,
        reason: str,
    ) -> "CloseIntent":
        """Create a position-originated close intent."""

        return cls(
            intent_id=new_internal_id("close"),
            instrument=instrument,
            position_id=position_id,
            quantity=quantity,
            reason=reason,
            created_at=utc_now(),
        )


@dataclass(frozen=True, slots=True)
class CloseRoutingResult:
    """Explicit outcome for a close intent routed through the core seams."""

    result_id: str
    close_intent_id: str
    verdict: CloseRoutingVerdict
    order_intent_id: str | None
    admitted_order_id: str | None
    reason: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        require_utc_datetime(self.created_at, "created_at")
        if self.verdict is CloseRoutingVerdict.ADMITTED and self.admitted_order_id is None:
            raise ValueError("admitted_close_route_requires_admitted_order_id")

    @classmethod
    def create(
        cls,
        *,
        close_intent_id: str,
        verdict: CloseRoutingVerdict,
        order_intent_id: str | None = None,
        admitted_order_id: str | None = None,
        reason: str | None = None,
    ) -> "CloseRoutingResult":
        """Create an explicit close-routing result with preserved lineage."""

        return cls(
            result_id=new_internal_id("close_route"),
            close_intent_id=close_intent_id,
            verdict=verdict,
            order_intent_id=order_intent_id,
            admitted_order_id=admitted_order_id,
            reason=reason,
            created_at=utc_now(),
        )

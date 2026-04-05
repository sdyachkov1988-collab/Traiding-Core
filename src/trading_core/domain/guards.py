"""Pre-execution guard outcomes and admissibility basis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from trading_core.domain.orders import OrderType, TimeInForce
from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now


class GuardVerdict(StrEnum):
    """Formal pre-execution guard verdict."""

    PASSED = "passed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ExecutionAdmissibilityBasis:
    """Execution-facing basis for formal admissibility checks only."""

    instrument_id: str
    quantity_step: Decimal
    price_step: Decimal
    min_quantity: Decimal
    min_notional: Decimal
    supported_order_types: tuple[OrderType, ...]
    supported_time_in_force: tuple[TimeInForce, ...]
    reference_price: Decimal


@dataclass(frozen=True, slots=True)
class GuardOutcome:
    """Formal guard outcome for an order intent."""

    guard_outcome_id: str
    verdict: GuardVerdict
    order_intent_id: str
    reason: str | None
    checked_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.checked_at, "checked_at")

    @classmethod
    def create(
        cls,
        *,
        verdict: GuardVerdict,
        order_intent_id: str,
        reason: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "GuardOutcome":
        """Build a formal guard outcome without crossing into execution."""

        return cls(
            guard_outcome_id=new_internal_id("guard"),
            verdict=verdict,
            order_intent_id=order_intent_id,
            reason=reason,
            checked_at=utc_now(),
            metadata=dict(metadata or {}),
        )

"""Order-intent primitives for the early order construction seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, require_utc_datetime, utc_now


class OrderSide(StrEnum):
    """Minimal order-side vocabulary."""

    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    """Minimal order-type vocabulary."""

    MARKET = "market"
    LIMIT = "limit"


class TimeInForce(StrEnum):
    """Minimal time-in-force vocabulary."""

    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """Executable intent produced after risk approval."""

    order_intent_id: str
    risk_decision_id: str
    instrument: InstrumentRef
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    limit_price: Decimal | None
    time_in_force: TimeInForce
    created_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.created_at, "created_at")

    @classmethod
    def create(
        cls,
        *,
        risk_decision_id: str,
        instrument: InstrumentRef,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        time_in_force: TimeInForce,
        limit_price: Decimal | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "OrderIntent":
        """Build an executable order intent downstream of risk approval."""

        return cls(
            order_intent_id=new_internal_id("ordint"),
            risk_decision_id=risk_decision_id,
            instrument=instrument,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            time_in_force=time_in_force,
            created_at=utc_now(),
            metadata=dict(metadata or {}),
        )

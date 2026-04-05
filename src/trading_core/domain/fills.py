"""Fill-side domain facts for the first working truth spine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, require_utc_datetime, utc_now
from trading_core.domain.orders import OrderSide


@dataclass(frozen=True, slots=True)
class Fill:
    """Execution fact recognized by the internal fill-driven spine.

    Fee semantics in the current build are intentionally explicit:

    - `fee` may be zero when no commission is charged
    - `fee` may be negative for rebate-style execution
    - on BUY, `SpotPositionEngine` folds the fee into cost basis under the
      current assembly-level policy `assembly_level_fee_in_cost_basis`
    - on SELL, `SpotPositionEngine` subtracts the fee from realized PnL
    """

    fill_id: str
    order_intent_id: str
    instrument: InstrumentRef
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    executed_at: datetime
    external_fill_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.executed_at, "executed_at")

    @property
    def gross_notional(self) -> Decimal:
        return self.quantity * self.price

    @classmethod
    def create(
        cls,
        *,
        order_intent_id: str,
        instrument: InstrumentRef,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal("0"),
        external_fill_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "Fill":
        """Create an immutable fill fact for downstream state updates.

        `fee` is intentionally flexible:

        - `0` is valid
        - negative values are valid and represent rebates
        - quantity and price must both be strictly positive
        """

        if quantity <= Decimal("0"):
            raise ValueError(f"quantity must be > 0, got {quantity}")
        if price <= Decimal("0"):
            raise ValueError(f"price must be > 0, got {price}")

        return cls(
            fill_id=new_internal_id("fill"),
            order_intent_id=order_intent_id,
            instrument=instrument,
            side=side,
            quantity=quantity,
            price=price,
            fee=fee,
            executed_at=utc_now(),
            external_fill_id=external_fill_id,
            metadata=dict(metadata or {}),
        )

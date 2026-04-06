"""Instrument and execution-facing basis for early order construction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.orders import OrderType, TimeInForce


@dataclass(frozen=True, slots=True)
class InstrumentExecutionSpec:
    """Minimal instrument specification needed to shape an order intent."""

    instrument_id: str
    quantity_step: Decimal
    price_step: Decimal
    supported_order_types: tuple[OrderType, ...]
    supported_time_in_force: tuple[TimeInForce, ...]
    min_order_quantity: Decimal = Decimal("0")
    default_order_type: OrderType = OrderType.LIMIT
    default_time_in_force: TimeInForce = TimeInForce.GTC

    def __post_init__(self) -> None:
        if self.quantity_step <= Decimal("0"):
            raise ValueError("quantity_step_must_be_positive")
        if self.price_step <= Decimal("0"):
            raise ValueError("price_step_must_be_positive")
        if self.min_order_quantity < Decimal("0"):
            raise ValueError("min_order_quantity_must_be_non_negative")
        if self.default_order_type not in self.supported_order_types:
            raise ValueError("default_order_type_must_be_supported")
        if self.default_time_in_force not in self.supported_time_in_force:
            raise ValueError("default_time_in_force_must_be_supported")


@dataclass(frozen=True, slots=True)
class ExecutionConstraintBasis:
    """Minimal execution-facing basis for order form construction only."""

    reference_price: Decimal
    preferred_limit_offset: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.reference_price <= Decimal("0"):
            raise ValueError("reference_price_must_be_positive")
        if self.preferred_limit_offset < Decimal("0"):
            raise ValueError("preferred_limit_offset_must_be_non_negative")

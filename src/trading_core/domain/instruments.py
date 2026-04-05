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


@dataclass(frozen=True, slots=True)
class ExecutionConstraintBasis:
    """Minimal execution-facing basis for order form construction only."""

    reference_price: Decimal
    preferred_limit_offset: Decimal = Decimal("0")

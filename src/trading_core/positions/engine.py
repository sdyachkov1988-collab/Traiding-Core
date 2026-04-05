"""Position truth updates for Package F."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.fills import Fill
from trading_core.domain.orders import OrderSide
from trading_core.domain.portfolio_state import Position


@dataclass(slots=True)
class SpotPositionEngine:
    """Maintain minimal spot position truth from fill facts only."""

    def apply(self, current: Position | None, fill: Fill) -> Position:
        """Return the next position truth after a fill."""

        position = current or Position.empty(instrument=fill.instrument)
        if fill.side is OrderSide.BUY:
            new_quantity = position.quantity + fill.quantity
            if new_quantity <= Decimal("0"):
                raise AssertionError("buy_fill_must_increase_position_quantity")
            total_cost = (
                position.quantity * position.average_entry_price
                + fill.quantity * fill.price
                + fill.fee
            )
            average_entry_price = total_cost / new_quantity
            realized_pnl = position.realized_pnl
        else:
            if fill.quantity > position.quantity:
                raise ValueError("sell_fill_exceeds_current_position_quantity")
            closed_quantity = fill.quantity
            realized_pnl = position.realized_pnl + (
                (fill.price - position.average_entry_price) * closed_quantity
            ) - fill.fee
            new_quantity = position.quantity - fill.quantity
            average_entry_price = (
                Decimal("0") if new_quantity <= Decimal("0") else position.average_entry_price
            )

        return Position(
            position_id=position.position_id,
            instrument=position.instrument,
            quantity=new_quantity,
            average_entry_price=average_entry_price,
            realized_pnl=realized_pnl,
            updated_at=fill.executed_at,
            metadata=position.metadata,
        )

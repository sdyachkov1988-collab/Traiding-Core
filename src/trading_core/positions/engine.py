"""Position truth updates for Package F."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.close_intent import CloseIntent
from trading_core.domain.fills import Fill
from trading_core.domain.orders import OrderSide
from trading_core.domain.portfolio_state import Position


@dataclass(slots=True)
class SpotPositionEngine:
    """Maintain minimal spot position truth from fill facts only."""

    def initiate_close(
        self,
        current: Position,
        *,
        quantity: Decimal | None = None,
        reason: str,
    ) -> CloseIntent:
        """Create a position-originated close intent without a new strategy cycle."""

        close_quantity = current.quantity if quantity is None else quantity
        if current.quantity <= Decimal("0"):
            raise ValueError("no_position_to_close")
        if close_quantity <= Decimal("0"):
            raise ValueError("close_quantity_must_be_positive")
        if close_quantity > current.quantity:
            raise ValueError("close_quantity_exceeds_current_position_quantity")

        return CloseIntent.create(
            instrument=current.instrument,
            position_id=current.position_id,
            quantity=close_quantity,
            reason=reason,
        )

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
            updated_at=max(position.updated_at, fill.executed_at),
            metadata=position.metadata,
        )

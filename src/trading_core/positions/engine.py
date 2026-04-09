"""Position truth updates for Package F."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.close_intent import CloseIntent
from trading_core.domain.fills import Fill
from trading_core.domain.orders import OrderSide
from trading_core.domain.portfolio_state import Position
from trading_core.observability import emit_structured_event


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
        if position.instrument.instrument_id != fill.instrument.instrument_id:
            raise ValueError("fill_instrument_does_not_match_current_position")
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

        next_position = Position(
            position_id=position.position_id,
            instrument=position.instrument,
            quantity=new_quantity,
            average_entry_price=average_entry_price,
            realized_pnl=realized_pnl,
            updated_at=max(position.updated_at, fill.executed_at),
            metadata=position.metadata,
        )
        emit_structured_event(
            logger_name=__name__,
            event_type="position_update",
            entity_type="position",
            entity_id=next_position.position_id,
            lineage_id=fill.fill_id,
            stage="position_state",
            lifecycle_step="position_updated",
            decision="apply_fill",
            outcome="updated",
            reason=fill.side.value,
            reason_code=fill.side.value,
            metadata={"instrument_id": fill.instrument.instrument_id},
        )
        return next_position

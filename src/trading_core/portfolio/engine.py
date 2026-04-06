"""Portfolio truth updates for Package F."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.common import new_internal_id
from trading_core.domain.fills import Fill
from trading_core.domain.orders import OrderSide
from trading_core.domain.portfolio_state import PortfolioState, Position


@dataclass(slots=True)
class SpotPortfolioEngine:
    """Maintain minimal portfolio truth from fills and positions only."""

    def apply(self, current: PortfolioState, fill: Fill, position: Position) -> PortfolioState:
        """Return the next portfolio state after a fill."""

        prev_position = current.positions.get(fill.instrument.instrument_id)

        if fill.side is OrderSide.BUY:
            next_cash_balance = current.cash_balance - fill.gross_notional - fill.fee
            if next_cash_balance < Decimal("0"):
                raise ValueError("buy_fill_exceeds_available_cash_balance")
        else:
            prev_quantity = prev_position.quantity if prev_position is not None else Decimal("0")
            if fill.quantity > prev_quantity:
                raise ValueError("sell_fill_exceeds_current_position_quantity")
            next_cash_balance = current.cash_balance + (fill.quantity * fill.price) - fill.fee

        next_positions = dict(current.positions)
        if position.quantity <= Decimal("0"):
            next_positions.pop(position.instrument.instrument_id, None)
        else:
            next_positions[position.instrument.instrument_id] = position

        previous_realized = prev_position.realized_pnl if prev_position is not None else Decimal("0")
        next_realized_pnl = current.realized_pnl - previous_realized + position.realized_pnl
        return PortfolioState(
            portfolio_state_id=new_internal_id("portfolio"),
            cash_balance=next_cash_balance,
            realized_pnl=next_realized_pnl,
            positions=next_positions,
            updated_at=fill.executed_at,
            metadata=current.metadata,
        )

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

        if fill.side is OrderSide.BUY:
            next_cash_balance = current.cash_balance - fill.gross_notional - fill.fee
        else:
            prev_position = current.positions.get(fill.instrument.instrument_id)
            prev_quantity = prev_position.quantity if prev_position is not None else Decimal("0")
            actually_sold = min(prev_quantity, fill.quantity)
            next_cash_balance = current.cash_balance + (actually_sold * fill.price) - fill.fee

        next_positions = dict(current.positions)
        next_positions[position.instrument.instrument_id] = position
        next_realized_pnl = sum(p.realized_pnl for p in next_positions.values())
        return PortfolioState(
            portfolio_state_id=new_internal_id("portfolio"),
            cash_balance=next_cash_balance,
            realized_pnl=next_realized_pnl,
            positions=next_positions,
            updated_at=fill.executed_at,
            metadata=current.metadata,
        )

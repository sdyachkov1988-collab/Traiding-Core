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
    """Maintain portfolio truth from fills and positions without discarding fill facts."""

    def apply(self, current: PortfolioState, fill: Fill, position: Position) -> PortfolioState:
        """Return the next portfolio state after a fill."""

        prev_position = current.positions.get(fill.instrument.instrument_id)
        conflict_flags: list[str] = []

        if fill.side is OrderSide.BUY:
            next_cash_balance = current.cash_balance - fill.gross_notional - fill.fee
            if next_cash_balance < Decimal("0"):
                conflict_flags.append("cash_balance_below_zero_after_fill")
        else:
            prev_quantity = prev_position.quantity if prev_position is not None else Decimal("0")
            if fill.quantity > prev_quantity:
                conflict_flags.append("sell_fill_exceeds_local_position_quantity")
            next_cash_balance = current.cash_balance + (fill.quantity * fill.price) - fill.fee

        next_positions = dict(current.positions)
        if position.quantity <= Decimal("0"):
            next_positions.pop(position.instrument.instrument_id, None)
        else:
            next_positions[position.instrument.instrument_id] = position

        previous_realized = prev_position.realized_pnl if prev_position is not None else Decimal("0")
        next_realized_pnl = current.realized_pnl - previous_realized + position.realized_pnl
        next_available_cash = min(next_cash_balance, Decimal("0")) if next_cash_balance < Decimal("0") else next_cash_balance
        next_reserved_cash = max(Decimal("0"), next_cash_balance - next_available_cash)
        next_balances = dict(current.balances)
        next_balances["cash"] = next_cash_balance
        position_cost_basis = sum(
            existing_position.quantity * existing_position.average_entry_price
            for existing_position in next_positions.values()
        )
        next_metadata = dict(current.metadata)
        if conflict_flags:
            next_metadata["reconcile_required"] = "true"
            next_metadata["reconcile_reasons"] = ",".join(conflict_flags)
        else:
            next_metadata.pop("reconcile_required", None)
            next_metadata.pop("reconcile_reasons", None)
        next_metadata.setdefault("equity_valuation_basis", "cash_plus_position_cost_basis")
        return PortfolioState(
            portfolio_state_id=new_internal_id("portfolio"),
            cash_balance=next_cash_balance,
            available_cash_balance=next_available_cash,
            reserved_cash_balance=next_reserved_cash,
            realized_pnl=next_realized_pnl,
            equity=next_cash_balance + position_cost_basis,
            balances=next_balances,
            positions=next_positions,
            updated_at=max(current.updated_at, fill.executed_at),
            metadata=next_metadata,
        )

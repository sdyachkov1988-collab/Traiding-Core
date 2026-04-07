"""Position and portfolio truth for the first fill-driven spine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, require_utc_datetime, utc_now


@dataclass(frozen=True, slots=True)
class Position:
    """Minimal position truth derived only from fills."""

    position_id: str
    instrument: InstrumentRef
    quantity: Decimal
    average_entry_price: Decimal
    realized_pnl: Decimal
    updated_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.updated_at, "updated_at")
        if self.quantity < Decimal("0"):
            raise ValueError("position_quantity_must_be_non_negative")
        if self.quantity == Decimal("0") and self.average_entry_price != Decimal("0"):
            raise ValueError("flat_position_must_not_have_cost_basis")
        if self.quantity > Decimal("0") and self.average_entry_price <= Decimal("0"):
            raise ValueError("open_position_must_have_positive_average_entry_price")

    @classmethod
    def empty(
        cls,
        *,
        instrument: InstrumentRef,
        metadata: Mapping[str, str] | None = None,
    ) -> "Position":
        return cls(
            position_id=new_internal_id("pos"),
            instrument=instrument,
            quantity=Decimal("0"),
            average_entry_price=Decimal("0"),
            realized_pnl=Decimal("0"),
            updated_at=utc_now(),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class PortfolioState:
    """Portfolio truth for the first fill-driven accounting spine."""

    portfolio_state_id: str
    cash_balance: Decimal
    available_cash_balance: Decimal
    reserved_cash_balance: Decimal
    realized_pnl: Decimal
    equity: Decimal
    balances: Mapping[str, Decimal]
    positions: Mapping[str, Position]
    updated_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.updated_at, "updated_at")
        if self.available_cash_balance < Decimal("0"):
            raise ValueError("available_cash_balance_must_be_non_negative")
        if self.reserved_cash_balance < Decimal("0"):
            raise ValueError("reserved_cash_balance_must_be_non_negative")
        if self.balances.get("cash") != self.cash_balance:
            raise ValueError("cash_balance_must_match_cash_ledger")
        if self.cash_balance >= Decimal("0"):
            if self.available_cash_balance + self.reserved_cash_balance != self.cash_balance:
                raise ValueError("cash_balances_must_reconcile")
        elif self.available_cash_balance != Decimal("0") or self.reserved_cash_balance != Decimal("0"):
            raise ValueError("negative_cash_balance_cannot_have_available_or_reserved_components")
        for instrument_id, position in self.positions.items():
            if instrument_id != position.instrument.instrument_id:
                raise ValueError("position_key_must_match_position_instrument_id")

    @classmethod
    def empty(
        cls,
        *,
        cash_balance: Decimal,
        metadata: Mapping[str, str] | None = None,
    ) -> "PortfolioState":
        return cls(
            portfolio_state_id=new_internal_id("portfolio"),
            cash_balance=cash_balance,
            available_cash_balance=cash_balance,
            reserved_cash_balance=Decimal("0"),
            realized_pnl=Decimal("0"),
            equity=cash_balance,
            balances={"cash": cash_balance},
            positions={},
            updated_at=utc_now(),
            metadata={
                "equity_valuation_basis": "cash_plus_position_cost_basis",
                **dict(metadata or {}),
            },
        )

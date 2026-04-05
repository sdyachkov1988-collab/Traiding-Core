"""Risk-layer verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, require_utc_datetime, utc_now
from trading_core.domain.orders import OrderSide


class RiskVerdict(StrEnum):
    """Minimal risk verdict vocabulary for Minimal Core v1."""

    APPROVED = "approved"
    CAPPED = "capped"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class InstrumentRiskBasis:
    """Minimal instrument-side basis used by the risk seam."""

    instrument_id: str
    min_order_quantity: Decimal
    max_order_quantity: Decimal
    quantity_step: Decimal
    instrument_tradable: bool = True


@dataclass(frozen=True, slots=True)
class PortfolioRiskBasis:
    """Minimal portfolio-side basis used by the risk seam."""

    available_capital: Decimal
    max_capital_per_trade: Decimal
    reference_price: Decimal
    current_position_quantity: Decimal = Decimal("0")
    portfolio_tradable: bool = True


@dataclass(frozen=True, slots=True)
class RiskDecision:
    """Separate downstream verdict for a strategy intent."""

    risk_decision_id: str
    verdict: RiskVerdict
    strategy_intent_id: str
    instrument: InstrumentRef
    side: OrderSide
    approved_quantity: Decimal | None
    rejection_reason: str | None
    created_at: datetime
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.created_at, "created_at")

    @classmethod
    def create(
        cls,
        *,
        verdict: RiskVerdict,
        strategy_intent_id: str,
        instrument: InstrumentRef,
        side: OrderSide,
        approved_quantity: Decimal | None = None,
        rejection_reason: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "RiskDecision":
        """Build a separate risk verdict linked to an upstream strategy intent."""

        return cls(
            risk_decision_id=new_internal_id("risk"),
            verdict=verdict,
            strategy_intent_id=strategy_intent_id,
            instrument=instrument,
            side=side,
            approved_quantity=approved_quantity,
            rejection_reason=rejection_reason,
            created_at=utc_now(),
            metadata=dict(metadata or {}),
        )

"""Strategy-side domain results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from trading_core.domain.common import InstrumentRef, new_internal_id, utc_now
from trading_core.domain.orders import OrderSide


@dataclass(frozen=True, slots=True)
class StrategyIntent:
    """Formal strategy-side decision result before risk review."""

    intent_id: str
    instrument: InstrumentRef
    side: OrderSide
    thesis: str
    confidence: Decimal
    created_at: datetime
    strategy_name: str
    context_id: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        instrument: InstrumentRef,
        side: OrderSide,
        thesis: str,
        confidence: Decimal,
        strategy_name: str,
        context_id: str,
        metadata: Mapping[str, str] | None = None,
    ) -> "StrategyIntent":
        """Build a strategy intent with internal lineage identity."""

        if not (Decimal("0") <= confidence <= Decimal("1")):
            raise ValueError(f"confidence must be in [0, 1], got {confidence}")

        return cls(
            intent_id=new_internal_id("intent"),
            instrument=instrument,
            side=side,
            thesis=thesis,
            confidence=confidence,
            created_at=utc_now(),
            strategy_name=strategy_name,
            context_id=context_id,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class NoAction:
    """Explicit no-trade result produced by the strategy seam."""

    context_id: str
    reason: str
    created_at: datetime
    strategy_name: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        context_id: str,
        reason: str,
        strategy_name: str,
        metadata: Mapping[str, str] | None = None,
    ) -> "NoAction":
        """Build an explicit no-action result."""

        return cls(
            context_id=context_id,
            reason=reason,
            created_at=utc_now(),
            strategy_name=strategy_name,
            metadata=dict(metadata or {}),
        )

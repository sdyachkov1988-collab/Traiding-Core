"""Reference strategy implementations for Package B."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from trading_core.contracts.strategy import StrategyResult
from trading_core.domain.context import MarketContext
from trading_core.domain.orders import OrderSide
from trading_core.domain.strategy import NoAction, StrategyIntent


@dataclass(slots=True)
class BarDirectionStrategy:
    """A minimal reference strategy based on bar direction."""

    strategy_name: str = "bar_direction"
    min_body_ratio: Decimal = Decimal("0.001")

    def evaluate(self, context: MarketContext) -> StrategyResult:
        """Return a strategy intent or explicit no-action from a valid context."""

        payload = context.latest_event.payload
        open_value = payload.get("open")
        close_value = payload.get("close")
        if open_value is None or close_value is None:
            return NoAction.create(
                context_id=context.context_id,
                reason="missing_open_or_close",
                strategy_name=self.strategy_name,
            )

        try:
            open_price = Decimal(open_value)
            close_price = Decimal(close_value)
        except InvalidOperation:
            return NoAction.create(
                context_id=context.context_id,
                reason="non_decimal_bar_values",
                strategy_name=self.strategy_name,
            )

        if open_price <= Decimal("0"):
            return NoAction.create(
                context_id=context.context_id,
                reason="non_positive_open",
                strategy_name=self.strategy_name,
            )

        body_ratio = abs(close_price - open_price) / open_price
        if body_ratio < self.min_body_ratio:
            return NoAction.create(
                context_id=context.context_id,
                reason="bar_body_too_small",
                strategy_name=self.strategy_name,
            )

        side = OrderSide.BUY if close_price > open_price else OrderSide.SELL
        return StrategyIntent.create(
            instrument=context.instrument,
            side=side,
            thesis="bar_direction_continuation",
            confidence=min(Decimal("1.0"), body_ratio),
            strategy_name=self.strategy_name,
            context_id=context.context_id,
            metadata={"source_event_id": context.latest_event.event_id},
        )

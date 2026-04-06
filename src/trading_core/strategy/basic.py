"""Reference strategy implementations for Package B."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from trading_core.contracts.strategy import StrategyResult
from trading_core.domain.context import MarketContext, Wave1MtfContext
from trading_core.domain.orders import OrderSide
from trading_core.domain.strategy import NoAction, StrategyIntent


@dataclass(slots=True)
class BarDirectionStrategy:
    """A legacy reference strategy based on bar direction."""

    strategy_name: str = "bar_direction"
    min_body_ratio: Decimal = Decimal("0.001")

    def evaluate(self, context: MarketContext) -> StrategyResult:
        """Return a strategy intent or explicit no-action from a valid context."""

        if any(is_ready is False for is_ready in context.readiness_flags.values()):
            return NoAction.create(
                context_id=context.context_id,
                reason="context_not_ready",
                strategy_name=self.strategy_name,
            )

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


@dataclass(slots=True)
class MtfBarAlignmentStrategy:
    """The active Wave 1 strategy operating on the formal MTF contract only."""

    strategy_name: str = "mtf_bar_alignment"
    entry_timeframe: str = "15m"
    trend_timeframe: str = "1h"
    min_entry_body_ratio: Decimal = Decimal("0.001")

    def evaluate(self, context: Wave1MtfContext) -> StrategyResult:
        """Return an intent only when Wave 1 MTF input is ready and aligned."""

        if any(is_ready is False for is_ready in context.readiness_flags.values()):
            return NoAction.create(
                context_id=context.context_id,
                reason="context_not_ready",
                strategy_name=self.strategy_name,
            )

        if context.closed_bar_only is False:
            return NoAction.create(
                context_id=context.context_id,
                reason="closed_bar_only_required",
                strategy_name=self.strategy_name,
            )

        if context.no_lookahead_safe is False:
            return NoAction.create(
                context_id=context.context_id,
                reason="lookahead_boundary_not_safe",
                strategy_name=self.strategy_name,
            )

        entry_bar = context.entry_bar
        trend_bar = context.trend_bar
        if entry_bar is None or trend_bar is None:
            return NoAction.create(
                context_id=context.context_id,
                reason="required_timeframe_missing",
                strategy_name=self.strategy_name,
            )

        if entry_bar.open <= Decimal("0") or trend_bar.open <= Decimal("0"):
            return NoAction.create(
                context_id=context.context_id,
                reason="non_positive_open",
                strategy_name=self.strategy_name,
            )

        entry_body_ratio = abs(entry_bar.close - entry_bar.open) / entry_bar.open
        if entry_body_ratio < self.min_entry_body_ratio:
            return NoAction.create(
                context_id=context.context_id,
                reason="entry_bar_body_too_small",
                strategy_name=self.strategy_name,
            )

        entry_side = OrderSide.BUY if entry_bar.close > entry_bar.open else OrderSide.SELL
        trend_side = OrderSide.BUY if trend_bar.close > trend_bar.open else OrderSide.SELL
        if entry_side is not trend_side:
            return NoAction.create(
                context_id=context.context_id,
                reason="timeframe_direction_mismatch",
                strategy_name=self.strategy_name,
            )

        trend_body_ratio = abs(trend_bar.close - trend_bar.open) / trend_bar.open
        confidence = min(Decimal("1.0"), max(entry_body_ratio, trend_body_ratio))
        return StrategyIntent.create(
            instrument=context.instrument,
            side=entry_side,
            thesis="mtf_alignment_continuation",
            confidence=confidence,
            strategy_name=self.strategy_name,
            context_id=context.context_id,
            metadata={
                "entry_timeframe": self.entry_timeframe,
                "trend_timeframe": self.trend_timeframe,
            },
        )

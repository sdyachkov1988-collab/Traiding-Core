"""Reference strategy implementations for Package B."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from trading_core.contracts.strategy import StrategyResult
from trading_core.domain.context import MarketContext, Wave1MtfContext
from trading_core.domain.orders import OrderSide
from trading_core.domain.strategy import NoAction, StrategyIntent
from trading_core.domain.timeframe import TimeframeContext


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
    """MTF strategy that accepts the Wave 1 seam and the formal next-stage context."""

    strategy_name: str = "mtf_bar_alignment"
    entry_timeframe: str = "15m"
    trend_timeframe: str = "1h"
    min_entry_body_ratio: Decimal = Decimal("0.001")

    def evaluate(self, context: TimeframeContext | Wave1MtfContext) -> StrategyResult:
        """Return an intent only when the provided MTF context is ready and aligned."""

        readiness_flags = context.readiness_flags
        if isinstance(context, TimeframeContext):
            required_readiness = (
                readiness_flags.get(self.entry_timeframe) is not False
                and readiness_flags.get(self.trend_timeframe) is not False
            )
            closed_bar_only = context.metadata.get("closed_bar_ok") != "false"
            no_lookahead_safe = context.metadata.get("lookahead_violation") != "true"
            entry_bar = context.bars.get(self.entry_timeframe)
            trend_bar = context.bars.get(self.trend_timeframe)
        else:
            required_readiness = all(
                readiness_flags.get(flag_name) is not False
                for flag_name in ("entry_ready", "trend_ready", "context_ready")
            )
            closed_bar_only = context.closed_bar_only
            no_lookahead_safe = context.no_lookahead_safe
            entry_bar = context.entry_bar
            trend_bar = context.trend_bar

        if not required_readiness:
            return NoAction.create(
                context_id=context.context_id,
                reason="context_not_ready",
                strategy_name=self.strategy_name,
            )

        if not closed_bar_only:
            return NoAction.create(
                context_id=context.context_id,
                reason="closed_bar_only_required",
                strategy_name=self.strategy_name,
            )

        if not no_lookahead_safe:
            return NoAction.create(
                context_id=context.context_id,
                reason="lookahead_boundary_not_safe",
                strategy_name=self.strategy_name,
            )

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

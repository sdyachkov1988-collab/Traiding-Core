"""Strategy implementations for documented seams."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.contracts.strategy import StrategyResult
from trading_core.domain.context import Wave1MtfContext
from trading_core.domain.orders import OrderSide
from trading_core.domain.strategy import NoAction, StrategyIntent
from trading_core.domain.timeframe import TimeframeContext


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

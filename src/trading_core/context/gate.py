"""Context Gate implementation for Wave 2B."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.context.policies import FreshnessPolicy
from trading_core.domain.gate import GateOutcome, GateVerdict
from trading_core.domain.timeframe import TimeframeContext


@dataclass(slots=True)
class ContextGate:
    """Single admission barrier before strategy evaluation."""

    warmup_bars: int
    freshness_policy: FreshnessPolicy
    required_timeframes: tuple[str, ...] | None = None

    def check(self, context: TimeframeContext | None) -> GateOutcome:
        """Return a formal gate decision for the current context."""

        if context is None:
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="context_not_ready",
                bars_seen=0,
                warmup_required=self.warmup_bars,
            )

        required_timeframes = self.required_timeframes or context.timeframe_set
        entry_history_depth = context.history_depths.get(context.entry_timeframe, 0)
        missing_timeframes = [
            timeframe for timeframe in required_timeframes if timeframe not in context.bars
        ]
        if missing_timeframes:
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="required_timeframe_missing",
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
            )

        non_closed_timeframes = [
            timeframe
            for timeframe in required_timeframes
            if context.bars[timeframe].is_closed is not True
        ]
        if non_closed_timeframes:
            return GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason="required_timeframe_not_closed",
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
            )

        if any(
            context.freshness_flags.get(timeframe) is False
            for timeframe in required_timeframes
        ):
            return GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason="stale_context",
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
            )

        if any(
            context.readiness_flags.get(timeframe) is False
            for timeframe in required_timeframes
        ):
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="timeframe_not_ready",
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
            )

        bars_seen = min(
            context.history_depths.get(timeframe, 0)
            for timeframe in required_timeframes
        )
        warmup_values = [self.warmup_bars]
        warmup_values.extend(
            int(threshold.split(":")[1])
            for threshold in context.metadata.get("warmup_thresholds", "").split(",")
            if threshold
        )
        warmup_required = max(warmup_values)
        if bars_seen < warmup_required:
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="warmup_not_reached",
                bars_seen=bars_seen,
                warmup_required=warmup_required,
            )

        return GateOutcome.create(
            verdict=GateVerdict.ADMITTED,
            reason=None,
            bars_seen=bars_seen,
            warmup_required=warmup_required,
        )

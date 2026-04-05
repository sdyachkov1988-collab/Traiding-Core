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

    def check(self, context: TimeframeContext | None) -> GateOutcome:
        """Return a formal gate decision for the current context."""

        if context is None:
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="context_not_ready",
                bars_seen=0,
                warmup_required=self.warmup_bars,
            )

        if any(is_fresh is False for is_fresh in context.freshness_flags.values()):
            return GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason="stale_context",
                bars_seen=len(context.bars),
                warmup_required=self.warmup_bars,
            )

        if any(is_ready is False for is_ready in context.readiness_flags.values()):
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="timeframe_not_ready",
                bars_seen=len(context.bars),
                warmup_required=self.warmup_bars,
            )

        bars_seen = len(context.bars)
        if bars_seen < self.warmup_bars:
            return GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason="warmup_not_reached",
                bars_seen=bars_seen,
                warmup_required=self.warmup_bars,
            )

        return GateOutcome.create(
            verdict=GateVerdict.ADMITTED,
            reason=None,
            bars_seen=bars_seen,
            warmup_required=self.warmup_bars,
        )

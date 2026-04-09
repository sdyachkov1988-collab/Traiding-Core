"""Context Gate implementation for Wave 2B."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.context.policies import FreshnessPolicy
from trading_core.domain.gate import GateOutcome, GateReason, GateVerdict
from trading_core.domain.timeframe import TimeframeContext
from trading_core.observability import emit_structured_event


@dataclass(slots=True)
class ContextGate:
    """Single admission barrier before strategy evaluation."""

    warmup_bars: int
    freshness_policy: FreshnessPolicy
    required_timeframes: tuple[str, ...] | None = None

    def check(self, context: TimeframeContext | None) -> GateOutcome:
        """Return a formal gate decision for the current context."""

        if context is None:
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=GateReason.CONTEXT_NOT_READY,
                bars_seen=0,
                warmup_required=self.warmup_bars,
                ),
                context=None,
            )

        required_timeframes = (
            context.timeframe_set if self.required_timeframes is None else self.required_timeframes
        )
        if not required_timeframes:
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=GateReason.REQUIRED_COMPONENT_UNAVAILABLE,
                bars_seen=0,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )
        if context.entry_timeframe not in required_timeframes:
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=GateReason.REQUIRED_COMPONENT_UNAVAILABLE,
                bars_seen=0,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )
        entry_history_depth = context.history_depths.get(context.entry_timeframe, 0)
        missing_timeframes = [
            timeframe for timeframe in required_timeframes if timeframe not in context.bars
        ]
        if missing_timeframes:
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=GateReason.REQUIRED_TIMEFRAME_MISSING,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if context.metadata.get("required_component_unavailable") == "true":
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=GateReason.REQUIRED_COMPONENT_UNAVAILABLE,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if context.metadata.get("session_restricted") == "true":
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=GateReason.SESSION_RESTRICTED,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if context.metadata.get("maintenance_restricted") == "true":
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=GateReason.MAINTENANCE_RESTRICTED,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        non_closed_timeframes = [
            timeframe
            for timeframe in required_timeframes
            if context.bars[timeframe].is_closed is not True
        ]
        if non_closed_timeframes:
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=GateReason.REQUIRED_TIMEFRAME_NOT_CLOSED,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if context.metadata.get("data_gap_detected") == "true":
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=GateReason.DATA_GAP_DETECTED,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if context.metadata.get("lookahead_violation") == "true":
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=GateReason.LOOKAHEAD_VIOLATION,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if any(
            timeframe not in context.freshness_flags
            or context.freshness_flags[timeframe] is False
            for timeframe in required_timeframes
        ):
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=(
                    GateReason.REQUIRED_COMPONENT_UNAVAILABLE
                    if any(timeframe not in context.freshness_flags for timeframe in required_timeframes)
                    else GateReason.STALE_CONTEXT
                ),
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        if any(
            timeframe not in context.readiness_flags
            or context.readiness_flags[timeframe] is False
            for timeframe in required_timeframes
        ):
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=(
                    GateReason.REQUIRED_COMPONENT_UNAVAILABLE
                    if any(timeframe not in context.readiness_flags for timeframe in required_timeframes)
                    else GateReason.TIMEFRAME_NOT_READY
                ),
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )

        bars_seen = min(
            context.history_depths.get(timeframe, 0)
            for timeframe in required_timeframes
        )
        warmup_values = [self.warmup_bars]
        try:
            warmup_values.extend(
                int(threshold.split(":")[1])
                for threshold in context.metadata.get("warmup_thresholds", "").split(",")
                if threshold and ":" in threshold and threshold.split(":")[1]
            )
        except (TypeError, ValueError, IndexError):
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.REJECTED,
                reason=GateReason.REQUIRED_COMPONENT_UNAVAILABLE,
                bars_seen=entry_history_depth,
                warmup_required=self.warmup_bars,
                ),
                context=context,
            )
        warmup_required = max(warmup_values)
        if bars_seen < warmup_required:
            return self._log_outcome(
                GateOutcome.create(
                verdict=GateVerdict.DEFERRED,
                reason=GateReason.WARMUP_NOT_REACHED,
                bars_seen=bars_seen,
                warmup_required=warmup_required,
                ),
                context=context,
            )

        return self._log_outcome(
            GateOutcome.create(
            verdict=GateVerdict.ADMITTED,
            reason=None,
            bars_seen=bars_seen,
            warmup_required=warmup_required,
            ),
            context=context,
        )

    def _log_outcome(
        self,
        outcome: GateOutcome,
        *,
        context: TimeframeContext | None,
    ) -> GateOutcome:
        metadata = {
            "bars_seen": str(outcome.bars_seen),
            "warmup_required": str(outcome.warmup_required),
        }
        if context is not None:
            metadata["instrument_id"] = context.instrument_id
            metadata["entry_timeframe"] = context.entry_timeframe
            metadata["required_timeframes"] = ",".join(self._required_timeframes(context))
        emit_structured_event(
            logger_name=__name__,
            event_type="context_gate",
            entity_type="gate_outcome",
            entity_id=outcome.outcome_id,
            lineage_id=None if context is None else context.context_id,
            stage="context_gate",
            lifecycle_step="gate_checked",
            decision=outcome.verdict.value,
            outcome=outcome.verdict.value,
            reason=None if outcome.reason is None else outcome.reason.value,
            reason_code=outcome.reason_code,
            metadata=metadata,
        )
        return outcome

    def _required_timeframes(self, context: TimeframeContext) -> tuple[str, ...]:
        return (
            context.timeframe_set
            if self.required_timeframes is None
            else self.required_timeframes
        )

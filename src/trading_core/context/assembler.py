"""Assembler for Wave 2A timeframe contexts."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.context.policies import BarAlignmentPolicy, ClosedBarPolicy, FreshnessPolicy
from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain.common import utc_now
from trading_core.domain.timeframe import TimeframeContext


@dataclass(slots=True)
class TimeframeContextAssembler:
    """Assemble a read-only timeframe context from store + policies."""

    instrument_id: str
    store: InstrumentTimeframeStore
    alignment_policy: BarAlignmentPolicy
    closed_bar_policy: ClosedBarPolicy
    freshness_policy: FreshnessPolicy
    warmup_thresholds: dict[str, int] | None = None

    def assemble(self) -> TimeframeContext | None:
        """Return a valid timeframe context or None when not ready."""

        bars = self.store.get_bars()
        now = utc_now()
        history_depths = self.store.get_history_depths()
        readiness_flags = {
            timeframe: timeframe in bars
            for timeframe in self.alignment_policy.required_timeframes
        }
        if not all(readiness_flags.values()):
            return None

        required_bars = {
            timeframe: bars[timeframe]
            for timeframe in self.alignment_policy.required_timeframes
        }
        for bar in required_bars.values():
            if not self.closed_bar_policy.is_valid_closed_bar(bar):
                return None

        if not self.alignment_policy.is_aligned(required_bars):
            return None

        freshness_flags = {
            timeframe: self.freshness_policy.is_fresh(bar, now)
            for timeframe, bar in required_bars.items()
        }
        metadata = {
            "required_timeframes": ",".join(self.alignment_policy.required_timeframes),
        }
        if self.warmup_thresholds:
            metadata["warmup_thresholds"] = ",".join(
                f"{timeframe}:{bars_required}"
                for timeframe, bars_required in sorted(self.warmup_thresholds.items())
            )
        return TimeframeContext.create(
            instrument_id=self.instrument_id,
            entry_timeframe=self.alignment_policy.entry_timeframe,
            timeframe_set=self.alignment_policy.required_timeframes,
            bars=required_bars,
            history_depths=history_depths,
            readiness_flags=readiness_flags,
            freshness_flags=freshness_flags,
            alignment_policy=self.alignment_policy.policy_name,
            metadata=metadata,
        )

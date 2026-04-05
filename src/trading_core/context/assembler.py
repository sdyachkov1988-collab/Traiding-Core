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

    def assemble(self) -> TimeframeContext | None:
        """Return a valid timeframe context or None when not ready."""

        bars = self.store.get_bars()
        if not self.alignment_policy.is_aligned(bars):
            return None

        for bar in bars.values():
            if not self.closed_bar_policy.is_valid_closed_bar(bar):
                return None

        now = utc_now()
        readiness_flags = {
            timeframe: timeframe in bars
            for timeframe in self.alignment_policy.required_timeframes
        }
        freshness_flags = {
            timeframe: self.freshness_policy.is_fresh(bar, now)
            for timeframe, bar in bars.items()
        }
        return TimeframeContext.create(
            instrument_id=self.instrument_id,
            entry_timeframe=self.alignment_policy.entry_timeframe,
            timeframe_set=self.alignment_policy.required_timeframes,
            bars=bars,
            readiness_flags=readiness_flags,
            freshness_flags=freshness_flags,
            alignment_policy=self.alignment_policy.policy_name,
        )

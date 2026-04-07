"""Assembler for Wave 2A timeframe contexts."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.context.policies import BarAlignmentPolicy, ClosedBarPolicy, FreshnessPolicy
from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.domain.timeframe import TimeframeContext


@dataclass(slots=True)
class TimeframeContextAssembler:
    """Assemble a read-only timeframe context from store + policies."""

    instrument_id: str
    store: InstrumentTimeframeStore
    alignment_policy: BarAlignmentPolicy
    closed_bar_policy: ClosedBarPolicy
    freshness_policy: FreshnessPolicy
    instrument: InstrumentRef | None = None
    warmup_thresholds: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.store.instrument_id != self.instrument_id:
            raise ValueError("assembler_instrument_and_store_must_match")
        if self.instrument is not None and self.instrument.instrument_id != self.instrument_id:
            raise ValueError("assembler_instrument_ref_and_instrument_id_must_match")

    def assemble(self) -> TimeframeContext | None:
        """Return a valid timeframe context or None when not ready."""

        bars = self.store.get_bars()
        if not bars:
            return None

        now = utc_now()
        history_depths = {
            timeframe: self.store.get_history_depth(timeframe)
            for timeframe in self.alignment_policy.required_timeframes
        }
        gap_flags = self.store.get_gap_flags()
        readiness_flags = {
            timeframe: timeframe in bars
            for timeframe in self.alignment_policy.required_timeframes
        }
        required_bars = {
            timeframe: bars[timeframe]
            for timeframe in self.alignment_policy.required_timeframes
            if timeframe in bars
        }
        closed_bar_ok = all(
            self.closed_bar_policy.is_valid_closed_bar(bar)
            for bar in required_bars.values()
        )
        alignment_ok = all(readiness_flags.values()) and self.alignment_policy.is_aligned(required_bars)

        freshness_flags = {
            timeframe: (
                self.freshness_policy.is_fresh(required_bars[timeframe], now)
                if timeframe in required_bars
                else False
            )
            for timeframe in self.alignment_policy.required_timeframes
        }
        metadata = {
            "required_timeframes": ",".join(self.alignment_policy.required_timeframes),
            "alignment_ok": "true" if alignment_ok else "false",
            "closed_bar_ok": "true" if closed_bar_ok else "false",
        }
        if not all(readiness_flags.values()):
            metadata["required_component_unavailable"] = "true"
        if all(readiness_flags.values()) and not alignment_ok:
            metadata["lookahead_violation"] = "true"
        if any(gap_flags.get(timeframe, False) for timeframe in self.alignment_policy.required_timeframes):
            metadata["data_gap_detected"] = "true"
        if self.warmup_thresholds:
            metadata["warmup_thresholds"] = ",".join(
                f"{timeframe}:{bars_required}"
                for timeframe, bars_required in sorted(self.warmup_thresholds.items())
            )
        return TimeframeContext.create(
            instrument_id=self.instrument_id,
            instrument=self._resolve_instrument(required_bars),
            entry_timeframe=self.alignment_policy.entry_timeframe,
            timeframe_set=self.alignment_policy.required_timeframes,
            bars=required_bars,
            history_depths=history_depths,
            readiness_flags=readiness_flags,
            freshness_flags=freshness_flags,
            alignment_policy=self.alignment_policy.policy_name,
            metadata=metadata,
        )

    def _resolve_instrument(self, bars: dict[str, object]) -> InstrumentRef:
        if self.instrument is not None:
            return self.instrument
        return InstrumentRef(
            instrument_id=self.instrument_id,
            symbol=self.instrument_id,
            venue="unknown",
        )

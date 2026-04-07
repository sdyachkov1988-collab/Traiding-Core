from __future__ import annotations

from datetime import timedelta, timezone
from decimal import Decimal

from trading_core.context.assembler import TimeframeContextAssembler
from trading_core.context.gate import ContextGate
from trading_core.context.policies import BarAlignmentPolicy, ClosedBarPolicy, FreshnessPolicy
from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain import (
    GateOutcome,
    GateReason,
    GateVerdict,
    InstrumentRef,
    OrderSide,
    StrategyIntent,
    TimeframeSyncEvent,
)
from trading_core.domain.common import utc_now
from trading_core.domain.timeframe import ClosedBar, TimeframeContext


def make_closed_bar(
    *,
    timeframe: str,
    age_seconds: int = 0,
    bar_time=None,
) -> ClosedBar:
    now = utc_now().replace(second=0, microsecond=0)
    if bar_time is None and timeframe.endswith("m"):
        minutes = int(timeframe[:-1])
        aligned_minute = (now.minute // minutes) * minutes
        bar_time = now.replace(minute=aligned_minute)
    elif bar_time is None and timeframe.endswith("h"):
        hours = int(timeframe[:-1])
        aligned_hour = (now.hour // hours) * hours
        bar_time = now.replace(hour=aligned_hour, minute=0)
    elif bar_time is None:
        bar_time = now

    return ClosedBar(
        timeframe=timeframe,
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("95"),
        close=Decimal("105"),
        volume=Decimal("10"),
        bar_time=bar_time - timedelta(seconds=age_seconds),
        is_closed=True,
    )


def make_context(
    *,
    readiness_flags: dict[str, bool] | None = None,
    freshness_flags: dict[str, bool] | None = None,
    bars: dict[str, ClosedBar] | None = None,
    history_depths: dict[str, int] | None = None,
    metadata: dict[str, str] | None = None,
) -> TimeframeContext:
    now = utc_now().replace(second=0, microsecond=0)
    bar_map = bars or {
        "15m": make_closed_bar(timeframe="15m", bar_time=now - timedelta(minutes=15)),
        "1h": make_closed_bar(timeframe="1h", bar_time=now - timedelta(hours=1)),
    }
    return TimeframeContext.create(
        instrument_id="btc-usdt",
        entry_timeframe="15m",
        timeframe_set=("15m", "1h"),
        bars=bar_map,
        history_depths=history_depths or {"15m": len(bar_map), "1h": 1},
        readiness_flags=readiness_flags or {"15m": True, "1h": True},
        freshness_flags=freshness_flags or {"15m": True, "1h": True},
        alignment_policy="bar_alignment_policy",
        metadata=metadata or {},
    )


def test_context_gate_defers_none_context() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=7200))

    outcome = gate.check(None)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.CONTEXT_NOT_READY


def test_context_gate_rejects_stale_context() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(freshness_flags={"15m": False, "1h": True})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.STALE_CONTEXT


def test_context_gate_defers_when_timeframe_not_ready() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(readiness_flags={"15m": True, "1h": False})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.TIMEFRAME_NOT_READY


def test_context_gate_defers_when_required_timeframe_is_missing_from_context() -> None:
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=300),
        required_timeframes=("15m", "1h"),
    )
    context = make_context(
        bars={"15m": make_closed_bar(timeframe="15m")},
        readiness_flags={"15m": True, "1h": True},
        freshness_flags={"15m": True, "1h": True},
    )

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.REQUIRED_TIMEFRAME_MISSING


def test_context_gate_does_not_admit_context_missing_readiness_flags() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context()
    object.__setattr__(context, "readiness_flags", {"15m": True})

    outcome = gate.check(context)

    assert outcome.verdict != GateVerdict.ADMITTED
    assert outcome.reason == GateReason.REQUIRED_COMPONENT_UNAVAILABLE


def test_context_gate_does_not_admit_context_missing_freshness_flags() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context()
    object.__setattr__(context, "freshness_flags", {"15m": True})

    outcome = gate.check(context)

    assert outcome.verdict != GateVerdict.ADMITTED
    assert outcome.reason == GateReason.REQUIRED_COMPONENT_UNAVAILABLE


def test_context_gate_defers_when_warmup_not_reached() -> None:
    gate = ContextGate(warmup_bars=3, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(history_depths={"15m": 2, "1h": 1})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.WARMUP_NOT_REACHED


def test_context_gate_admits_when_all_conditions_are_met() -> None:
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=300),
        required_timeframes=("15m", "1h"),
    )
    context = make_context(history_depths={"15m": 2, "1h": 2})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.ADMITTED
    assert outcome.reason is None


def test_gate_outcome_contains_bars_seen_and_warmup_required() -> None:
    gate = ContextGate(warmup_bars=3, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(history_depths={"15m": 4, "1h": 4})

    outcome = gate.check(context)

    assert isinstance(outcome, GateOutcome)
    assert outcome.bars_seen == 4
    assert outcome.warmup_required == 3
    assert outcome.checked_at.tzinfo == timezone.utc


def test_context_gate_uses_context_warmup_thresholds_when_higher_than_default() -> None:
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=300),
        required_timeframes=("15m", "1h"),
    )
    context = make_context(history_depths={"15m": 3, "1h": 3})
    object.__setattr__(context, "metadata", {"warmup_thresholds": "15m:4,1h:2"})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.WARMUP_NOT_REACHED
    assert outcome.warmup_required == 4


def test_context_gate_rejects_malformed_warmup_threshold_metadata() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(history_depths={"15m": 3, "1h": 3}, metadata={"warmup_thresholds": "15m:not-a-number"})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.REQUIRED_COMPONENT_UNAVAILABLE


def test_context_gate_rejects_empty_required_timeframes_config() -> None:
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=300),
        required_timeframes=(),
    )

    outcome = gate.check(make_context())

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.REQUIRED_COMPONENT_UNAVAILABLE


def test_context_gate_rejects_entry_timeframe_outside_required_timeframes() -> None:
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=300),
        required_timeframes=("1h",),
    )

    outcome = gate.check(make_context())

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.REQUIRED_COMPONENT_UNAVAILABLE


def test_context_gate_rejects_lookahead_violation_from_context_metadata() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(metadata={"lookahead_violation": "true"})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.LOOKAHEAD_VIOLATION


def test_context_gate_defers_on_session_restriction() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(metadata={"session_restricted": "true"})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.SESSION_RESTRICTED
    assert outcome.reason_code == "session_restricted"


def test_context_gate_rejects_on_maintenance_restriction() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(metadata={"maintenance_restricted": "true"})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.MAINTENANCE_RESTRICTED
    assert outcome.reason_code == "maintenance_restricted"


def test_context_gate_defers_on_explicit_data_gap_signal() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(metadata={"data_gap_detected": "true"})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.DATA_GAP_DETECTED


def test_context_gate_defers_on_data_gap_from_assembled_context() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now().replace(second=0, microsecond=0)
    first_entry_bar_time = now - timedelta(minutes=45)
    second_entry_bar_time = now - timedelta(minutes=15)
    hourly_bar_time = second_entry_bar_time.replace(minute=0)
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m", bar_time=first_entry_bar_time),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m", bar_time=second_entry_bar_time),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=make_closed_bar(timeframe="1h", bar_time=hourly_bar_time),
        )
    )
    assembler = TimeframeContextAssembler(
        instrument_id="btc-usdt",
        store=store,
        alignment_policy=BarAlignmentPolicy(
            entry_timeframe="15m",
            required_timeframes=("15m", "1h"),
        ),
        closed_bar_policy=ClosedBarPolicy(),
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
    )
    gate = ContextGate(
        warmup_bars=1,
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
        required_timeframes=("15m", "1h"),
    )

    context = assembler.assemble()
    outcome = gate.check(context)

    assert context is not None
    assert context.metadata["data_gap_detected"] == "true"
    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.DATA_GAP_DETECTED


def test_context_gate_assembler_keeps_missing_required_component_for_gate_reasoning() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m"),
        )
    )
    assembler = TimeframeContextAssembler(
        instrument_id="btc-usdt",
        store=store,
        alignment_policy=BarAlignmentPolicy(
            entry_timeframe="15m",
            required_timeframes=("15m", "1h"),
        ),
        closed_bar_policy=ClosedBarPolicy(),
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
    )
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
        required_timeframes=("15m", "1h"),
    )

    context = assembler.assemble()
    outcome = gate.check(context)

    assert context is not None
    assert context.readiness_flags == {"15m": True, "1h": False}
    assert context.metadata["required_component_unavailable"] == "true"
    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == GateReason.REQUIRED_TIMEFRAME_MISSING


def test_context_gate_rejects_lookahead_violation_from_assembler_metadata() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now().replace(minute=15, second=0, microsecond=0)
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m", bar_time=now),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=make_closed_bar(timeframe="1h", bar_time=now),
        )
    )
    assembler = TimeframeContextAssembler(
        instrument_id="btc-usdt",
        store=store,
        alignment_policy=BarAlignmentPolicy(
            entry_timeframe="15m",
            required_timeframes=("15m", "1h"),
        ),
        closed_bar_policy=ClosedBarPolicy(),
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
    )
    gate = ContextGate(
        warmup_bars=1,
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
        required_timeframes=("15m", "1h"),
    )

    context = assembler.assemble()
    outcome = gate.check(context)

    assert context is not None
    assert context.metadata["lookahead_violation"] == "true"
    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == GateReason.LOOKAHEAD_VIOLATION


def test_gate_verdict_strenum_values_are_correct() -> None:
    assert GateVerdict.ADMITTED.value == "admitted"
    assert GateVerdict.DEFERRED.value == "deferred"
    assert GateVerdict.REJECTED.value == "rejected"


def test_gate_reason_strenum_values_are_correct() -> None:
    assert GateReason.CONTEXT_NOT_READY.value == "context_not_ready"
    assert GateReason.REQUIRED_TIMEFRAME_MISSING.value == "required_timeframe_missing"
    assert GateReason.DATA_GAP_DETECTED.value == "data_gap_detected"
    assert GateReason.LOOKAHEAD_VIOLATION.value == "lookahead_violation"
    assert GateReason.SESSION_RESTRICTED.value == "session_restricted"
    assert GateReason.MAINTENANCE_RESTRICTED.value == "maintenance_restricted"


def test_admitted_context_can_flow_into_strategy_intent() -> None:
    def evaluate_timeframe_context(context: TimeframeContext) -> StrategyIntent:
        entry_bar = context.bars[context.entry_timeframe]
        side = OrderSide.BUY if entry_bar.close > entry_bar.open else OrderSide.SELL
        return StrategyIntent.create(
            instrument=InstrumentRef(
                instrument_id=context.instrument_id,
                symbol="BTCUSDT",
                venue="binance",
            ),
            side=side,
            thesis="mtf_gate_admitted",
            confidence=Decimal("0.5"),
            strategy_name="inline_timeframe_strategy",
            context_id=context.context_id,
        )

    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now().replace(second=0, microsecond=0)
    first_entry_bar = make_closed_bar(timeframe="15m", bar_time=now - timedelta(minutes=90))
    second_entry_bar = make_closed_bar(
        timeframe="15m",
        bar_time=first_entry_bar.bar_time + timedelta(minutes=15),
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=first_entry_bar,
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=second_entry_bar,
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=make_closed_bar(
                timeframe="1h",
                bar_time=second_entry_bar.bar_time.replace(minute=0) - timedelta(hours=1),
            ),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=make_closed_bar(
                timeframe="1h",
                bar_time=second_entry_bar.bar_time.replace(minute=0),
            ),
        )
    )
    context = TimeframeContextAssembler(
        instrument_id="btc-usdt",
        store=store,
        alignment_policy=BarAlignmentPolicy(
            entry_timeframe="15m",
            required_timeframes=("15m", "1h"),
        ),
        closed_bar_policy=ClosedBarPolicy(),
        freshness_policy=FreshnessPolicy(max_age_seconds=7200),
    ).assemble()
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=7200))

    assert context is not None
    outcome = gate.check(context)
    strategy_intent = evaluate_timeframe_context(context)

    assert outcome.verdict == GateVerdict.ADMITTED
    assert isinstance(strategy_intent, StrategyIntent)
    assert strategy_intent.side == OrderSide.BUY

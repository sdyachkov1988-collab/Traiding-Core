from __future__ import annotations

from datetime import timedelta, timezone
from decimal import Decimal

from trading_core.context.assembler import TimeframeContextAssembler
from trading_core.context.gate import ContextGate
from trading_core.context.policies import BarAlignmentPolicy, ClosedBarPolicy, FreshnessPolicy
from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain import (
    GateOutcome,
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
) -> TimeframeContext:
    bar_map = bars or {
        "15m": make_closed_bar(timeframe="15m"),
        "1h": make_closed_bar(timeframe="1h"),
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
    )


def test_context_gate_defers_none_context() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=7200))

    outcome = gate.check(None)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == "context_not_ready"


def test_context_gate_rejects_stale_context() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(freshness_flags={"15m": False, "1h": True})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.REJECTED
    assert outcome.reason == "stale_context"


def test_context_gate_defers_when_timeframe_not_ready() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(readiness_flags={"15m": True, "1h": False})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == "timeframe_not_ready"


def test_context_gate_defers_when_warmup_not_reached() -> None:
    gate = ContextGate(warmup_bars=3, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(history_depths={"15m": 2, "1h": 1})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.DEFERRED
    assert outcome.reason == "warmup_not_reached"


def test_context_gate_admits_when_all_conditions_are_met() -> None:
    gate = ContextGate(warmup_bars=2, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(history_depths={"15m": 2, "1h": 1})

    outcome = gate.check(context)

    assert outcome.verdict == GateVerdict.ADMITTED
    assert outcome.reason is None


def test_gate_outcome_contains_bars_seen_and_warmup_required() -> None:
    gate = ContextGate(warmup_bars=3, freshness_policy=FreshnessPolicy(max_age_seconds=300))
    context = make_context(history_depths={"15m": 4, "1h": 1})

    outcome = gate.check(context)

    assert isinstance(outcome, GateOutcome)
    assert outcome.bars_seen == 4
    assert outcome.warmup_required == 3
    assert outcome.checked_at.tzinfo == timezone.utc


def test_gate_verdict_strenum_values_are_correct() -> None:
    assert GateVerdict.ADMITTED.value == "admitted"
    assert GateVerdict.DEFERRED.value == "deferred"
    assert GateVerdict.REJECTED.value == "rejected"


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
    first_entry_bar = make_closed_bar(timeframe="15m")
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

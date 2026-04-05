from __future__ import annotations

from datetime import timedelta, timezone
from decimal import Decimal

import pytest

from trading_core.context import (
    BarAlignmentPolicy,
    ClosedBarPolicy,
    FreshnessPolicy,
    InstrumentTimeframeStore,
    TimeframeContextAssembler,
)
from trading_core.domain import ClosedBar, TimeframeContext, TimeframeSyncEvent
from trading_core.domain.common import utc_now


def make_closed_bar(
    *,
    timeframe: str,
    age_seconds: int = 0,
    bar_time=None,
) -> ClosedBar:
    now = utc_now().replace(second=0, microsecond=0)
    if bar_time is None:
        if timeframe.endswith("m"):
            minutes = int(timeframe[:-1])
            aligned_minute = (now.minute // minutes) * minutes
            bar_time = now.replace(minute=aligned_minute)
        elif timeframe.endswith("h"):
            hours = int(timeframe[:-1])
            aligned_hour = (now.hour // hours) * hours
            bar_time = now.replace(hour=aligned_hour, minute=0)
        else:
            bar_time = now

    return ClosedBar(
        timeframe=timeframe,
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("95"),
        close=Decimal("105"),
        volume=Decimal("10"),
        bar_time=(bar_time - timedelta(seconds=age_seconds)) if age_seconds else bar_time,
        is_closed=True,
    )


def test_closed_bar_uses_decimal_fields_and_utc_datetime() -> None:
    bar = make_closed_bar(timeframe="15m")

    assert isinstance(bar.open, Decimal)
    assert isinstance(bar.close, Decimal)
    assert isinstance(bar.volume, Decimal)
    assert bar.bar_time.tzinfo == timezone.utc
    assert bar.is_closed is True


def test_instrument_timeframe_store_updates_and_returns_latest_bar() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    bar = make_closed_bar(timeframe="15m")
    event = TimeframeSyncEvent.create(
        instrument_id="btc-usdt",
        timeframe="15m",
        bar=bar,
    )

    store.update(event)

    assert store.get_bar("15m") == bar
    assert store.get_bars()["15m"] == bar
    assert store.get_history_depth("15m") == 1


def test_instrument_timeframe_store_rejects_non_monotonic_bar_updates() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    newer_bar = make_closed_bar(timeframe="15m")
    older_bar = make_closed_bar(timeframe="15m", age_seconds=60)
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=newer_bar,
        )
    )

    with pytest.raises(ValueError, match="timeframe_bar_time_must_be_monotonic"):
        store.update(
            TimeframeSyncEvent.create(
                instrument_id="btc-usdt",
                timeframe="15m",
                bar=older_bar,
            )
        )


def test_bar_alignment_policy_is_false_when_required_timeframes_missing() -> None:
    policy = BarAlignmentPolicy(entry_timeframe="15m", required_timeframes=("15m", "1h"))
    bars = {"15m": make_closed_bar(timeframe="15m")}

    assert policy.is_aligned(bars) is False


def test_bar_alignment_policy_is_true_when_all_required_timeframes_exist() -> None:
    policy = BarAlignmentPolicy(entry_timeframe="15m", required_timeframes=("15m", "1h"))
    now = utc_now().replace(minute=15, second=0, microsecond=0)
    bars = {
        "15m": make_closed_bar(timeframe="15m", bar_time=now),
        "1h": make_closed_bar(timeframe="1h", bar_time=now.replace(minute=0)),
    }

    assert policy.is_aligned(bars) is True


def test_bar_alignment_policy_is_false_when_parent_period_is_misaligned() -> None:
    policy = BarAlignmentPolicy(entry_timeframe="15m", required_timeframes=("15m", "1h"))
    now = utc_now().replace(minute=15, second=0, microsecond=0)
    bars = {
        "15m": make_closed_bar(timeframe="15m", bar_time=now),
        "1h": make_closed_bar(timeframe="1h", bar_time=now),
    }

    assert policy.is_aligned(bars) is False


def test_freshness_policy_returns_false_for_stale_bar() -> None:
    policy = FreshnessPolicy(max_age_seconds=60)
    stale_bar = make_closed_bar(timeframe="15m", age_seconds=120)

    assert policy.is_fresh(stale_bar, utc_now()) is False


def test_freshness_policy_returns_true_for_fresh_bar() -> None:
    policy = FreshnessPolicy(max_age_seconds=60)
    fresh_bar = make_closed_bar(timeframe="15m", bar_time=utc_now() - timedelta(seconds=10))

    assert policy.is_fresh(fresh_bar, utc_now()) is True


def test_timeframe_context_assembler_returns_none_when_alignment_not_met() -> None:
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

    assert assembler.assemble() is None


def test_timeframe_context_assembler_returns_context_when_ready() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    for timeframe in ("15m", "1h"):
        store.update(
            TimeframeSyncEvent.create(
                instrument_id="btc-usdt",
                timeframe=timeframe,
                bar=make_closed_bar(timeframe=timeframe),
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

    context = assembler.assemble()

    assert isinstance(context, TimeframeContext)
    assert context is not None
    assert context.instrument_id == "btc-usdt"
    assert context.entry_timeframe == "15m"


def test_timeframe_context_contains_readiness_and_freshness_flags() -> None:
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
            bar=make_closed_bar(timeframe="1h", bar_time=now.replace(minute=0)),
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

    context = assembler.assemble()

    assert context is not None
    assert context.readiness_flags == {"15m": True, "1h": True}
    assert context.freshness_flags == {"15m": True, "1h": True}
    assert context.history_depths == {"15m": 1, "1h": 1}


def test_timeframe_sync_event_updates_store_and_enables_context_assembly() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
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

    assert assembler.assemble() is None

    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m"),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=make_closed_bar(timeframe="1h"),
        )
    )

    context = assembler.assemble()

    assert context is not None
    assert set(context.bars) == {"15m", "1h"}


def test_timeframe_context_assembler_carries_history_depth_from_store() -> None:
    store = InstrumentTimeframeStore("btc-usdt")
    now = utc_now().replace(second=0, microsecond=0)
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m", bar_time=now.replace(minute=0)),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="15m",
            bar=make_closed_bar(timeframe="15m", bar_time=now.replace(minute=15)),
        )
    )
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=make_closed_bar(timeframe="1h", bar_time=now.replace(minute=0)),
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

    context = assembler.assemble()

    assert context is not None
    assert context.history_depths["15m"] == 2

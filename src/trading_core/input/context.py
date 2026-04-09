"""Concrete early context assembly for Package A."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from trading_core.context.policies import parent_period_start, timeframe_to_seconds
from trading_core.context.store import InstrumentTimeframeStore
from trading_core.domain.common import InstrumentRef
from trading_core.domain.context import Wave1MtfContext
from trading_core.domain.events import EventKind, MarketEvent
from trading_core.domain.timeframe import ClosedBar, TimeframeSyncEvent


@dataclass(slots=True)
class Wave1MtfContextAssembler:
    """Assemble a minimal Wave 1 MTF input object from canonical stored bars."""

    instrument: InstrumentRef
    store: InstrumentTimeframeStore
    entry_timeframe: str = "15m"
    trend_timeframe: str = "1h"

    def __post_init__(self) -> None:
        if self.store.instrument_id != self.instrument.instrument_id:
            raise ValueError("assembler_instrument_and_store_must_match")

    def assemble(self, event: MarketEvent) -> Wave1MtfContext:
        """Return the phase-scoped MTF input used by the active Wave 1 path."""

        self._validate_event_instrument(event)
        self._sync_store_from_event(event)
        entry_bar = self.store.get_bar(self.entry_timeframe)
        trend_bar = self.store.get_bar(self.trend_timeframe)
        readiness_flags = {
            "event_received": True,
            "entry_ready": entry_bar is not None,
            "trend_ready": trend_bar is not None,
            "context_ready": entry_bar is not None and trend_bar is not None,
        }
        closed_bar_only = all(
            bar is not None and bar.is_closed is True
            for bar in (entry_bar, trend_bar)
        )
        no_lookahead_safe = False
        if entry_bar is not None and trend_bar is not None:
            entry_seconds = timeframe_to_seconds(self.entry_timeframe)
            trend_seconds = timeframe_to_seconds(self.trend_timeframe)
            if trend_seconds >= entry_seconds and trend_seconds % entry_seconds == 0:
                no_lookahead_safe = (
                    trend_bar.bar_time
                    == parent_period_start(entry_bar.bar_time, self.trend_timeframe)
                )
        return Wave1MtfContext.create(
            instrument=self.instrument,
            entry_timeframe=self.entry_timeframe,
            trend_timeframe=self.trend_timeframe,
            entry_bar=entry_bar,
            trend_bar=trend_bar,
            closed_bar_only=closed_bar_only,
            no_lookahead_safe=no_lookahead_safe,
            readiness_flags=readiness_flags,
            metadata={
                "instrument_symbol": self.instrument.symbol,
                "source_event_id": event.event_id,
            },
        )

    def _validate_event_instrument(self, event: MarketEvent) -> None:
        if event.instrument.instrument_id != self.instrument.instrument_id:
            raise ValueError("event_instrument_and_assembler_must_match")
        if event.instrument.instrument_id != self.store.instrument_id:
            raise ValueError("event_instrument_and_store_must_match")

    def _sync_store_from_event(self, event: MarketEvent) -> None:
        if event.event_kind is not EventKind.BAR:
            return

        timeframe = event.payload.get("timeframe")
        if timeframe not in {self.entry_timeframe, self.trend_timeframe}:
            return

        self.store.update(
            TimeframeSyncEvent.create(
                instrument_id=event.instrument.instrument_id,
                timeframe=timeframe,
                bar=self._closed_bar_from_event(event),
                received_at=event.observed_at,
            )
        )

    def _closed_bar_from_event(self, event: MarketEvent) -> ClosedBar:
        try:
            timeframe = event.payload["timeframe"]
            open_price = Decimal(event.payload["open"])
            high_price = Decimal(event.payload["high"])
            low_price = Decimal(event.payload["low"])
            close_price = Decimal(event.payload["close"])
            volume = Decimal(event.payload["volume"])
        except KeyError as exc:
            raise ValueError(f"bar_event_missing_payload_field:{exc.args[0]}") from exc
        except InvalidOperation as exc:
            raise ValueError("bar_event_payload_must_be_decimal_compatible") from exc

        return ClosedBar(
            timeframe=timeframe,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            bar_time=event.event_time,
            is_closed=True,
        )

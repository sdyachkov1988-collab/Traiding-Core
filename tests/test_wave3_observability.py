from __future__ import annotations

import json
import logging
from decimal import Decimal

import pytest

from trading_core.context import InstrumentTimeframeStore
from trading_core.context.assembler import TimeframeContextAssembler
from trading_core.context.gate import ContextGate
from trading_core.context.policies import BarAlignmentPolicy, ClosedBarPolicy, FreshnessPolicy
from trading_core.domain import (
    AdmittedOrder,
    ClosedBar,
    ExecutionAdmissibilityBasis,
    ExecutionConstraintBasis,
    ExecutionReportKind,
    ExternalStartupBasis,
    InstrumentExecutionSpec,
    InstrumentRiskBasis,
    InstrumentRef,
    PortfolioState,
    PortfolioRiskBasis,
    TimeframeContext,
    TimeInForce,
    TimeframeSyncEvent,
)
from trading_core.domain.gate import GateReason, GateVerdict
from trading_core.domain.common import utc_now
from trading_core.domain.orders import OrderType
from trading_core.execution import (
    ExecutionHandoff,
    MockExecutionAdapter,
    SimpleOrderIntentBuilder,
    SimplePreExecutionGuard,
)
from trading_core.input import DictEventNormalizer, Wave1MtfContextAssembler
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import SpotPositionEngine
from trading_core.reconciliation import SimpleStartupReconciler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.state import JsonFileStateStore
from trading_core.strategy import MtfBarAlignmentStrategy


def test_wave3_structured_logging_covers_key_transitions(
    caplog: pytest.LogCaptureFixture,
    tmp_path,
) -> None:
    caplog.set_level(logging.INFO)
    normalizer = DictEventNormalizer()
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    store = InstrumentTimeframeStore("btc-usdt")
    store.update(
        TimeframeSyncEvent.create(
            instrument_id="btc-usdt",
            timeframe="1h",
            bar=ClosedBar(
                timeframe="1h",
                open=Decimal("100"),
                high=Decimal("106"),
                low=Decimal("95"),
                close=Decimal("105"),
                volume=Decimal("12"),
                bar_time=utc_now().replace(minute=0, second=0, microsecond=0),
                is_closed=True,
            ),
        )
    )
    assembler = Wave1MtfContextAssembler(
        instrument=instrument,
        store=store,
        entry_timeframe="15m",
        trend_timeframe="1h",
    )
    strategy = MtfBarAlignmentStrategy(min_entry_body_ratio=Decimal("0.001"))
    gate = ContextGate(
        warmup_bars=1,
        freshness_policy=FreshnessPolicy(max_age_seconds=200000),
        required_timeframes=("15m", "1h"),
    )
    risk = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))
    builder = SimpleOrderIntentBuilder()
    guard = SimplePreExecutionGuard()
    adapter = MockExecutionAdapter(accept_orders=True)
    handoff = ExecutionHandoff(adapter=adapter)
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    state_store = JsonFileStateStore(tmp_path / "state" / "latest.json")
    reconciler = SimpleStartupReconciler()

    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {
                "timeframe": "15m",
                "open": "100",
                "high": "106",
                "low": "99",
                "close": "105",
                "volume": "10",
            },
        }
    )
    context = assembler.assemble(event)
    timeframe_context = TimeframeContext.create(
        instrument_id="btc-usdt",
        instrument=instrument,
        entry_timeframe="15m",
        timeframe_set=("15m", "1h"),
        bars={
            "15m": context.entry_bar,
            "1h": context.trend_bar,
        },
        history_depths={"15m": 1, "1h": 1},
        readiness_flags={"15m": True, "1h": True},
        freshness_flags={"15m": True, "1h": True},
        alignment_policy="bar_alignment_policy",
        metadata={"warmup_thresholds": "15m:1,1h:1"},
    )
    gate_outcome = gate.check(timeframe_context)
    assert gate_outcome.verdict is GateVerdict.ADMITTED
    intent = strategy.evaluate(context)
    decision = risk.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("105.00"),
        ),
    )
    order_intent = builder.build(
        decision=decision,
        instrument_spec=InstrumentExecutionSpec(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
        ),
        execution_basis=ExecutionConstraintBasis(
            reference_price=Decimal("105.00"),
            preferred_limit_offset=Decimal("0.20"),
        ),
    )
    guard_outcome = guard.check(
        intent=order_intent,
        basis=ExecutionAdmissibilityBasis(
            instrument_id="btc-usdt",
            quantity_step=Decimal("0.01"),
            price_step=Decimal("0.10"),
            min_quantity=Decimal("0.01"),
            min_notional=Decimal("10"),
            supported_order_types=(OrderType.LIMIT, OrderType.MARKET),
            supported_time_in_force=(TimeInForce.GTC, TimeInForce.IOC),
            reference_price=Decimal("105.00"),
        ),
    )
    admitted_order = AdmittedOrder.create(order_intent=order_intent, guard_outcome=guard_outcome)
    reports = handoff.place(admitted_order)
    accepted_report = next(report for report in reports if report.kind is ExecutionReportKind.ACCEPTED)
    fill = handoff.materialize_fill(admitted_order, accepted_report, fee=Decimal("0.25"))
    position = position_engine.apply(None, fill)
    portfolio = portfolio_engine.apply(PortfolioState.empty(cash_balance=Decimal("1000")), fill, position)
    snapshot = state_store.save_with_fill_marker(portfolio, fill.fill_id)
    reconciler.reconcile(
        snapshot,
        ExternalStartupBasis.create(
            cash_balance=portfolio.cash_balance,
            available_cash_balance=portfolio.available_cash_balance,
            reserved_cash_balance=portfolio.reserved_cash_balance,
            realized_pnl=portfolio.realized_pnl,
            equity=portfolio.equity,
            positions={},
            order_picture={},
        ),
    )

    payloads = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name.startswith("trading_core.")
    ]

    assert {
        "strategy_intent",
        "context_gate",
        "risk_decision",
        "order_intent",
        "guard_outcome",
        "execution_report",
        "fill_fact",
        "position_update",
        "portfolio_update",
        "reconciliation_start",
        "reconciliation_outcome",
    }.issubset({payload["event_type"] for payload in payloads})
    for payload in payloads:
        assert "timestamp" in payload
        assert "event_type" in payload
        assert "entity_type" in payload
        assert "decision" in payload
        assert "outcome" in payload
        assert "reason" in payload
        assert "reason_code" in payload
        assert "stage" in payload or "lifecycle_step" in payload
        assert "entity_id" in payload or "lineage_id" in payload

    gate_payloads = [payload for payload in payloads if payload["event_type"] == "context_gate"]
    assert any(payload["outcome"] == "admitted" for payload in gate_payloads)
    assert all(payload["entity_type"] == "gate_outcome" for payload in gate_payloads)

    reconciliation_start_payloads = [
        payload for payload in payloads if payload["event_type"] == "reconciliation_start"
    ]
    assert len(reconciliation_start_payloads) == 1
    reconciliation_start_payload = reconciliation_start_payloads[0]
    assert reconciliation_start_payload["entity_type"] == "startup_reconciliation"
    assert "entity_id" in reconciliation_start_payload
    assert reconciliation_start_payload["entity_id"].startswith("reconcile_start_")
    assert reconciliation_start_payload["lineage_id"] == "startup_reconciliation"


def test_wave3_context_gate_logging_covers_formal_defer_reason(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    gate = ContextGate(
        warmup_bars=2,
        freshness_policy=FreshnessPolicy(max_age_seconds=300),
    )

    outcome = gate.check(None)

    assert outcome.verdict is GateVerdict.DEFERRED
    assert outcome.reason is GateReason.CONTEXT_NOT_READY
    payloads = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "trading_core.context.gate"
    ]
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["event_type"] == "context_gate"
    assert payload["entity_type"] == "gate_outcome"
    assert payload["stage"] == "context_gate"
    assert payload["lifecycle_step"] == "gate_checked"
    assert payload["decision"] == "deferred"
    assert payload["outcome"] == "deferred"
    assert payload["reason"] == "context_not_ready"
    assert payload["reason_code"] == "context_not_ready"

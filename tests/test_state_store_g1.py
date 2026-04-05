from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from trading_core.domain import PortfolioState
from trading_core.domain.common import InstrumentRef
from trading_core.domain.fills import Fill
from trading_core.domain.orders import OrderSide
from trading_core.domain.portfolio_state import Position
from trading_core.domain.state import FillDedupCheckpoint
from trading_core.execution import IdempotentFillProcessor
from trading_core.state import JsonFileStateStore


def test_json_file_state_store_round_trips_portfolio_snapshot(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state" / "latest.json")
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    position = Position.empty(instrument=instrument)
    position = Position(
        position_id=position.position_id,
        instrument=position.instrument,
        quantity=Decimal("0.50"),
        average_entry_price=Decimal("101"),
        realized_pnl=Decimal("3.2"),
        updated_at=position.updated_at,
        metadata={"source": "test"},
    )
    portfolio = PortfolioState(
        portfolio_state_id="portfolio_1",
        cash_balance=Decimal("950"),
        realized_pnl=Decimal("3.2"),
        positions={"btc-usdt": position},
        updated_at=position.updated_at,
        metadata={"env": "paper"},
    )

    saved = store.save(portfolio)
    loaded = store.load_latest()

    assert loaded is not None
    assert loaded.snapshot_id == saved.snapshot_id
    assert loaded.portfolio_state.cash_balance == Decimal("950")
    assert loaded.portfolio_state.positions["btc-usdt"].average_entry_price == Decimal("101")
    assert loaded.metadata["accounting_policy"] == "assembly_level_fee_in_cost_basis"


def test_json_file_state_store_returns_none_when_empty(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state" / "latest.json")

    assert store.load_latest() is None


def test_json_file_state_store_writes_json_payload(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state" / "latest.json")
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    store.save(portfolio)
    raw = json.loads((tmp_path / "state" / "latest.json").read_text(encoding="utf-8"))

    assert raw["portfolio_state"]["cash_balance"] == "1000"
    assert raw["metadata"]["storage_format"] == "json"


def test_json_file_state_store_does_not_leave_tmp_file_after_save(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    store.save(portfolio)

    assert target_path.exists()
    assert not target_path.with_suffix(".tmp").exists()


def test_json_file_state_store_save_with_fill_marker_persists_fill_id(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    snapshot = store.save_with_fill_marker(portfolio, "fill_abc123")
    raw = json.loads(target_path.read_text(encoding="utf-8"))

    assert snapshot.last_processed_fill_id == "fill_abc123"
    assert raw["last_processed_fill_id"] == "fill_abc123"
    assert raw["fill_dedup_checkpoint"] is None


def test_json_file_state_store_round_trips_explicit_fill_dedup_checkpoint(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    checkpoint = FillDedupCheckpoint(
        seen_fill_ids=("fill_1", "fill_2"),
        seen_external_fill_ids=("ext_1",),
        seen_fallback_keys=(("ord_1", "btc-usdt", "buy", "0.1", "100", "0"),),
    )

    snapshot = store.save_with_fill_marker(
        portfolio,
        "fill_2",
        dedup_checkpoint=checkpoint,
    )
    loaded = store.load_latest()

    assert snapshot.fill_dedup_checkpoint == checkpoint
    assert loaded is not None
    assert loaded.fill_dedup_checkpoint == checkpoint


def test_json_file_state_store_load_latest_remains_compatible_with_old_format(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    store.save(portfolio)
    loaded = store.load_latest()

    assert loaded is not None
    assert loaded.last_processed_fill_id is None
    assert loaded.fill_dedup_checkpoint is None


def test_json_file_state_store_save_with_fill_marker_does_not_leave_tmp_file(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    store.save_with_fill_marker(portfolio, "fill_abc123")

    assert target_path.exists()
    assert not target_path.with_suffix(".tmp").exists()


def test_state_store_last_processed_fill_id_can_be_restored_into_fill_processor(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )

    store.save_with_fill_marker(portfolio, fill.fill_id)
    snapshot = JsonFileStateStore(target_path).load_latest()
    assert snapshot is not None

    restarted_processor = IdempotentFillProcessor()
    restarted_processor.restore_processed_fill_id(snapshot.last_processed_fill_id)

    try:
        restarted_processor.accept(fill)
    except ValueError as exc:
        assert str(exc) == "Duplicate fill_id received by FillProcessor"
    else:
        raise AssertionError("Expected duplicate fill_id to be rejected after restart restore")


def test_state_store_restart_restore_rejects_duplicate_external_fill_id(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
        external_fill_id="ext_123",
    )
    fill_processor.accept(first)
    store.save_with_fill_marker(
        portfolio,
        first.fill_id,
        dedup_checkpoint=fill_processor.checkpoint(),
    )
    snapshot = JsonFileStateStore(target_path).load_latest()
    assert snapshot is not None

    restarted_processor = IdempotentFillProcessor()
    restarted_processor.restore_checkpoint(snapshot.fill_dedup_checkpoint)

    duplicate_external = Fill.create(
        order_intent_id="ordint_2",
        instrument=first.instrument,
        side=first.side,
        quantity=first.quantity,
        price=first.price,
        fee=first.fee,
        external_fill_id="ext_123",
    )

    with pytest.raises(ValueError, match="Duplicate external_fill_id"):
        restarted_processor.accept(duplicate_external)


def test_state_store_restart_restore_rejects_duplicate_fallback_identity(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    fill_processor.accept(first)
    store.save_with_fill_marker(
        portfolio,
        first.fill_id,
        dedup_checkpoint=fill_processor.checkpoint(),
    )
    snapshot = JsonFileStateStore(target_path).load_latest()
    assert snapshot is not None

    restarted_processor = IdempotentFillProcessor()
    restarted_processor.restore_checkpoint(snapshot.fill_dedup_checkpoint)

    duplicate_fallback = Fill.create(
        order_intent_id="ordint_1",
        instrument=first.instrument,
        side=first.side,
        quantity=first.quantity,
        price=first.price,
        fee=first.fee,
    )

    with pytest.raises(ValueError, match="Duplicate fallback fill identity"):
        restarted_processor.accept(duplicate_fallback)


def test_state_store_restart_restore_accepts_distinct_fill_after_checkpoint_restore(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
        external_fill_id="ext_123",
    )
    fill_processor.accept(first)
    store.save_with_fill_marker(
        portfolio,
        first.fill_id,
        dedup_checkpoint=fill_processor.checkpoint(),
    )
    snapshot = JsonFileStateStore(target_path).load_latest()
    assert snapshot is not None

    restarted_processor = IdempotentFillProcessor()
    restarted_processor.restore_checkpoint(snapshot.fill_dedup_checkpoint)

    distinct_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=first.instrument,
        side=first.side,
        quantity=Decimal("0.10"),
        price=Decimal("101"),
        fee=Decimal("0"),
        external_fill_id="ext_456",
    )

    assert restarted_processor.accept(distinct_fill) is distinct_fill


def test_json_file_state_store_rejects_naive_datetime_during_deserialization(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "state" / "latest.json"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(
            {
                "snapshot_id": "snapshot_1",
                "saved_at": "2026-01-01T12:00:00",
                "last_processed_fill_id": None,
                "metadata": {"storage_format": "json"},
                "portfolio_state": {
                    "portfolio_state_id": "portfolio_1",
                    "cash_balance": "1000",
                    "realized_pnl": "0",
                    "updated_at": "2026-01-01T12:00:00",
                    "metadata": {},
                    "positions": {},
                },
            }
        ),
        encoding="utf-8",
    )

    try:
        JsonFileStateStore(target_path).load_latest()
    except TypeError as exc:
        assert str(exc) == "portfolio_state.updated_at must be timezone-aware UTC"
    else:
        raise AssertionError("Expected naive persisted datetime to be rejected")

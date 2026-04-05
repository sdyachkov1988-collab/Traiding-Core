from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from trading_core.domain import PortfolioState
from trading_core.domain.common import InstrumentRef
from trading_core.domain.portfolio_state import Position
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


def test_json_file_state_store_save_with_fill_marker_does_not_leave_tmp_file(
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    store.save_with_fill_marker(portfolio, "fill_abc123")

    assert target_path.exists()
    assert not target_path.with_suffix(".tmp").exists()

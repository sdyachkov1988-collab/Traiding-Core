from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from trading_core.domain import PortfolioState
from trading_core.domain.common import InstrumentRef
from trading_core.domain.execution import ExecutionReportKind
from trading_core.domain.portfolio_state import Position
from trading_core.domain.state import PersistedOrderRecord
from trading_core.state import JsonFileStateStore


def build_portfolio_state() -> PortfolioState:
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    position = Position.empty(instrument=instrument)
    return PortfolioState(
        portfolio_state_id="portfolio_1",
        cash_balance=Decimal("950"),
        available_cash_balance=Decimal("940"),
        reserved_cash_balance=Decimal("10"),
        realized_pnl=Decimal("3.2"),
        equity=Decimal("1000.5"),
        balances={"cash": Decimal("950"), "USDT": Decimal("950")},
        positions={"btc-usdt": Position(
            position_id=position.position_id,
            instrument=position.instrument,
            quantity=Decimal("0.50"),
            average_entry_price=Decimal("101"),
            realized_pnl=Decimal("3.2"),
            updated_at=position.updated_at,
            metadata={"source": "test"},
        )},
        updated_at=position.updated_at,
        metadata={"env": "paper"},
    )


def test_state_store_can_save_order_picture_without_fill_marker(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = build_portfolio_state()
    order_picture = {
        "ordint_1": PersistedOrderRecord(
            order_intent_id="ordint_1",
            external_order_id="mock_ordint_1",
            last_report_kind=ExecutionReportKind.ACKNOWLEDGED,
            observed_at=portfolio.updated_at,
            metadata={"source": "startup_snapshot"},
        )
    }

    snapshot = store.save_with_order_picture(portfolio, order_picture)
    loaded = store.load_latest()

    assert snapshot.last_processed_fill_id is None
    assert loaded is not None
    assert loaded.last_processed_fill_id is None
    assert loaded.order_picture == order_picture
    assert loaded.portfolio_state == portfolio


def test_state_store_order_picture_path_round_trips_restore_readable_snapshot(tmp_path: Path) -> None:
    target_path = tmp_path / "state" / "latest.json"
    store = JsonFileStateStore(target_path)
    portfolio = build_portfolio_state()
    order_picture = {
        "ordint_1": PersistedOrderRecord(
            order_intent_id="ordint_1",
            external_order_id="mock_ordint_1",
            last_report_kind=ExecutionReportKind.ACKNOWLEDGED,
            observed_at=portfolio.updated_at,
            reason=None,
            metadata={"source": "startup_snapshot"},
        ),
        "ordint_2": PersistedOrderRecord(
            order_intent_id="ordint_2",
            external_order_id=None,
            last_report_kind=ExecutionReportKind.REJECTED,
            observed_at=portfolio.updated_at,
            reason="adapter_rejected_submission",
            metadata={"source": "startup_snapshot"},
        ),
    }

    store.save_with_order_picture(portfolio, order_picture)
    restored = JsonFileStateStore(target_path).load_latest()

    assert restored is not None
    assert restored.order_picture["ordint_1"].last_report_kind is ExecutionReportKind.ACKNOWLEDGED
    assert restored.order_picture["ordint_2"].last_report_kind is ExecutionReportKind.REJECTED
    assert restored.order_picture["ordint_2"].reason == "adapter_rejected_submission"

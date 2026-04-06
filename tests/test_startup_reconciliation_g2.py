from __future__ import annotations

from decimal import Decimal

from trading_core.domain import (
    ExternalStartupBasis,
    ExternalStartupPosition,
    PortfolioState,
    Position,
    StartupReconciliationVerdict,
)
from trading_core.domain.common import InstrumentRef
from trading_core.domain.state import PersistedStateSnapshot
from trading_core.reconciliation import SimpleStartupReconciler


def build_snapshot() -> PersistedStateSnapshot:
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
        available_cash_balance=Decimal("940"),
        reserved_cash_balance=Decimal("10"),
        realized_pnl=Decimal("3.2"),
        equity=Decimal("1000.5"),
        balances={"cash": Decimal("950"), "USDT": Decimal("950")},
        positions={"btc-usdt": position},
        updated_at=position.updated_at,
        metadata={"env": "paper"},
    )
    return PersistedStateSnapshot.create(portfolio_state=portfolio)


def test_startup_reconciler_matches_equal_local_and_external_state() -> None:
    reconciler = SimpleStartupReconciler()
    snapshot = build_snapshot()
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("950"),
        positions={
            "btc-usdt": ExternalStartupPosition(
                instrument_id="btc-usdt",
                quantity=Decimal("0.50"),
            )
        },
    )

    result = reconciler.reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CONSISTENT
    assert result.reason is None


def test_startup_reconciler_flags_missing_local_snapshot() -> None:
    reconciler = SimpleStartupReconciler()
    external = ExternalStartupBasis.create(cash_balance=Decimal("950"))

    result = reconciler.reconcile(None, external)

    assert result.verdict == StartupReconciliationVerdict.INSUFFICIENT_DATA_OR_TIMEOUT
    assert result.reason == "no_local_snapshot"


def test_startup_reconciler_flags_cash_mismatch() -> None:
    reconciler = SimpleStartupReconciler()
    snapshot = build_snapshot()
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("951"),
        positions={
            "btc-usdt": ExternalStartupPosition(
                instrument_id="btc-usdt",
                quantity=Decimal("0.50"),
            )
        },
    )

    result = reconciler.reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CANNOT_RECONCILE
    assert result.reason == "cash_balance_mismatch"


def test_startup_reconciler_flags_position_quantity_mismatch() -> None:
    reconciler = SimpleStartupReconciler()
    snapshot = build_snapshot()
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("950"),
        positions={
            "btc-usdt": ExternalStartupPosition(
                instrument_id="btc-usdt",
                quantity=Decimal("0.55"),
            )
        },
    )

    result = reconciler.reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CANNOT_RECONCILE
    assert result.reason == "position_quantity_mismatch"


def test_startup_reconciler_matches_when_closed_position_is_absent_from_local_snapshot() -> None:
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    position = Position.empty(instrument=instrument)
    portfolio = PortfolioState(
        portfolio_state_id="portfolio_2",
        cash_balance=Decimal("1000"),
        available_cash_balance=Decimal("1000"),
        reserved_cash_balance=Decimal("0"),
        realized_pnl=Decimal("1.0"),
        equity=Decimal("1000"),
        balances={"cash": Decimal("1000")},
        positions={},
        updated_at=position.updated_at,
        metadata={"env": "paper"},
    )
    snapshot = PersistedStateSnapshot.create(portfolio_state=portfolio)
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("1000"),
        positions={},
    )

    result = SimpleStartupReconciler().reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CONSISTENT
    assert result.reason is None


def test_startup_reconciler_can_return_corrected_for_zero_quantity_local_position() -> None:
    instrument = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    position = Position.empty(instrument=instrument)
    zero_position = Position(
        position_id=position.position_id,
        instrument=position.instrument,
        quantity=Decimal("0"),
        average_entry_price=Decimal("0"),
        realized_pnl=Decimal("0"),
        updated_at=position.updated_at,
        metadata={},
    )
    portfolio = PortfolioState(
        portfolio_state_id="portfolio_3",
        cash_balance=Decimal("1000"),
        available_cash_balance=Decimal("1000"),
        reserved_cash_balance=Decimal("0"),
        realized_pnl=Decimal("0"),
        equity=Decimal("1000"),
        balances={"cash": Decimal("1000")},
        positions={"btc-usdt": zero_position},
        updated_at=position.updated_at,
        metadata={"env": "paper"},
    )
    snapshot = PersistedStateSnapshot.create(portfolio_state=portfolio)
    external = ExternalStartupBasis.create(cash_balance=Decimal("1000"), positions={})

    result = SimpleStartupReconciler().reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CORRECTED
    assert result.reason == "zero_quantity_positions_pruned"

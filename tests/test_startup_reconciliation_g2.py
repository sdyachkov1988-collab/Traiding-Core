from __future__ import annotations

from decimal import Decimal

from trading_core.domain import (
    ExternalStartupBasis,
    ExternalStartupOrderRecord,
    ExternalStartupPosition,
    PortfolioState,
    Position,
    StartupReconciliationVerdict,
)
from trading_core.domain.common import InstrumentRef
from trading_core.domain.execution import ExecutionReportKind
from trading_core.domain.state import PersistedOrderRecord, PersistedStateSnapshot
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
    return PersistedStateSnapshot.create(
        portfolio_state=portfolio,
        order_picture={
            "ordint_1": PersistedOrderRecord(
                order_intent_id="ordint_1",
                external_order_id="ext_1",
                last_report_kind=ExecutionReportKind.ACKNOWLEDGED,
                observed_at=position.updated_at,
                metadata={"source": "test"},
            )
        },
    )


def build_external_basis(snapshot: PersistedStateSnapshot) -> ExternalStartupBasis:
    portfolio = snapshot.portfolio_state
    return ExternalStartupBasis.create(
        cash_balance=portfolio.cash_balance,
        available_cash_balance=portfolio.available_cash_balance,
        reserved_cash_balance=portfolio.reserved_cash_balance,
        realized_pnl=portfolio.realized_pnl,
        equity=portfolio.equity,
        positions={
            instrument_id: ExternalStartupPosition(
                instrument_id=instrument_id,
                quantity=position.quantity,
            )
            for instrument_id, position in portfolio.positions.items()
        },
        order_picture={
            order_intent_id: ExternalStartupOrderRecord(
                order_intent_id=record.order_intent_id,
                external_order_id=record.external_order_id,
                last_report_kind=record.last_report_kind,
                reason=record.reason,
                metadata=record.metadata,
            )
            for order_intent_id, record in snapshot.order_picture.items()
        },
    )


def test_startup_reconciler_matches_equal_local_and_external_state() -> None:
    reconciler = SimpleStartupReconciler()
    snapshot = build_snapshot()
    external = build_external_basis(snapshot)

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
    external = build_external_basis(snapshot)
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("951"),
        available_cash_balance=external.available_cash_balance,
        reserved_cash_balance=external.reserved_cash_balance,
        realized_pnl=external.realized_pnl,
        equity=external.equity,
        positions=external.positions,
        order_picture=external.order_picture,
    )

    result = reconciler.reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CANNOT_RECONCILE
    assert result.reason == "cash_balance_mismatch"


def test_startup_reconciler_flags_position_quantity_mismatch() -> None:
    reconciler = SimpleStartupReconciler()
    snapshot = build_snapshot()
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("950"),
        available_cash_balance=Decimal("940"),
        reserved_cash_balance=Decimal("10"),
        realized_pnl=Decimal("3.2"),
        equity=Decimal("1000.5"),
        positions={
            "btc-usdt": ExternalStartupPosition(
                instrument_id="btc-usdt",
                quantity=Decimal("0.55"),
            )
        },
        order_picture=build_external_basis(snapshot).order_picture,
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
        available_cash_balance=Decimal("1000"),
        reserved_cash_balance=Decimal("0"),
        realized_pnl=Decimal("1.0"),
        equity=Decimal("1000"),
        positions={},
        order_picture={},
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
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("1000"),
        available_cash_balance=Decimal("1000"),
        reserved_cash_balance=Decimal("0"),
        realized_pnl=Decimal("0"),
        equity=Decimal("1000"),
        positions={},
        order_picture={},
    )

    result = SimpleStartupReconciler().reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CORRECTED
    assert result.reason == "zero_quantity_positions_pruned"


def test_startup_reconciler_does_not_hide_shared_instrument_mismatch_after_zero_quantity_prune() -> None:
    btc = InstrumentRef(
        instrument_id="btc-usdt",
        symbol="BTCUSDT",
        venue="binance",
    )
    eth = InstrumentRef(
        instrument_id="eth-usdt",
        symbol="ETHUSDT",
        venue="binance",
    )
    base = Position.empty(instrument=btc)
    btc_position = Position(
        position_id=base.position_id,
        instrument=btc,
        quantity=Decimal("0.50"),
        average_entry_price=Decimal("101"),
        realized_pnl=Decimal("0"),
        updated_at=base.updated_at,
        metadata={},
    )
    zero_eth = Position(
        position_id="pos_eth",
        instrument=eth,
        quantity=Decimal("0"),
        average_entry_price=Decimal("0"),
        realized_pnl=Decimal("0"),
        updated_at=base.updated_at,
        metadata={},
    )
    snapshot = PersistedStateSnapshot.create(
        portfolio_state=PortfolioState(
            portfolio_state_id="portfolio_4",
            cash_balance=Decimal("1000"),
            available_cash_balance=Decimal("1000"),
            reserved_cash_balance=Decimal("0"),
            realized_pnl=Decimal("0"),
            equity=Decimal("1000"),
            balances={"cash": Decimal("1000")},
            positions={"btc-usdt": btc_position, "eth-usdt": zero_eth},
            updated_at=base.updated_at,
            metadata={},
        )
    )
    external = ExternalStartupBasis.create(
        cash_balance=Decimal("1000"),
        available_cash_balance=Decimal("1000"),
        reserved_cash_balance=Decimal("0"),
        realized_pnl=Decimal("0"),
        equity=Decimal("1000"),
        positions={
            "btc-usdt": ExternalStartupPosition(
                instrument_id="btc-usdt",
                quantity=Decimal("0.60"),
            )
        },
        order_picture={},
    )

    result = SimpleStartupReconciler().reconcile(snapshot, external)

    assert result.verdict == StartupReconciliationVerdict.CANNOT_RECONCILE
    assert result.reason == "position_quantity_mismatch"


def test_startup_reconciler_flags_order_picture_mismatch() -> None:
    snapshot = build_snapshot()
    external = build_external_basis(snapshot)
    external = ExternalStartupBasis.create(
        cash_balance=external.cash_balance,
        available_cash_balance=external.available_cash_balance,
        reserved_cash_balance=external.reserved_cash_balance,
        realized_pnl=external.realized_pnl,
        equity=external.equity,
        positions=external.positions,
        order_picture={
            "ordint_1": ExternalStartupOrderRecord(
                order_intent_id="ordint_1",
                external_order_id="ext_1",
                last_report_kind=ExecutionReportKind.REJECTED,
                reason="adapter_rejected_submission",
            )
        },
    )

    result = SimpleStartupReconciler().reconcile(snapshot, external)

    assert result.verdict != StartupReconciliationVerdict.CONSISTENT
    assert result.reason == "order_picture_mismatch"


def test_startup_reconciler_flags_portfolio_level_picture_mismatch() -> None:
    snapshot = build_snapshot()
    external = build_external_basis(snapshot)
    external = ExternalStartupBasis.create(
        cash_balance=external.cash_balance,
        available_cash_balance=Decimal("939"),
        reserved_cash_balance=external.reserved_cash_balance,
        realized_pnl=external.realized_pnl,
        equity=external.equity,
        positions=external.positions,
        order_picture=external.order_picture,
    )

    result = SimpleStartupReconciler().reconcile(snapshot, external)

    assert result.verdict != StartupReconciliationVerdict.CONSISTENT
    assert result.reason == "available_cash_balance_mismatch"

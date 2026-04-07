from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from trading_core.domain import Fill, OrderSide, PortfolioState, Position
from trading_core.domain.common import InstrumentRef, utc_now
from trading_core.execution import IdempotentFillProcessor
from trading_core.portfolio import SpotPortfolioEngine
from trading_core.positions import SpotPositionEngine


def instrument() -> InstrumentRef:
    return InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")


def test_fill_driven_spine_builds_position_and_portfolio_from_buys() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("1"),
    )

    accepted_fill = fill_processor.accept(buy_fill)
    position = position_engine.apply(None, accepted_fill)
    portfolio = portfolio_engine.apply(portfolio, accepted_fill, position)

    assert position.quantity == Decimal("0.10")
    assert position.average_entry_price == Decimal("110")
    assert portfolio.cash_balance == Decimal("989")
    assert portfolio.positions["btc-usdt"].quantity == Decimal("0.10")


def test_portfolio_engine_marks_buy_fill_that_would_make_cash_negative_for_reconcile() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("100"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("2.00"),
        price=Decimal("60"),
        fee=Decimal("1"),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))

    updated_portfolio = portfolio_engine.apply(portfolio, buy_fill, position)

    assert updated_portfolio.cash_balance == Decimal("-21")
    assert updated_portfolio.metadata["reconcile_required"] == "true"
    assert "cash_balance_below_zero_after_fill" in updated_portfolio.metadata["reconcile_reasons"]


def test_conflicted_buy_fill_leaves_existing_portfolio_truth_unchanged() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    original_portfolio = PortfolioState.empty(cash_balance=Decimal("100"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("2.00"),
        price=Decimal("60"),
        fee=Decimal("1"),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))

    updated_portfolio = portfolio_engine.apply(original_portfolio, buy_fill, position)

    assert original_portfolio.cash_balance == Decimal("100")
    assert original_portfolio.positions == {}
    assert updated_portfolio.metadata["reconcile_required"] == "true"


def test_fill_driven_spine_realizes_pnl_only_from_sell_fill() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    sell_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.SELL,
        quantity=Decimal("0.04"),
        price=Decimal("120"),
        fee=Decimal("0.5"),
    )

    position = position_engine.apply(None, fill_processor.accept(buy_fill))
    portfolio = portfolio_engine.apply(portfolio, buy_fill, position)
    position = position_engine.apply(position, fill_processor.accept(sell_fill))
    portfolio = portfolio_engine.apply(portfolio, sell_fill, position)

    assert position.quantity == Decimal("0.06")
    assert position.realized_pnl == Decimal("0.3")
    assert portfolio.realized_pnl == Decimal("0.3")
    assert portfolio.cash_balance == Decimal("994.3")


def test_portfolio_engine_removes_zero_quantity_position_after_full_close() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    sell_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.SELL,
        quantity=Decimal("0.10"),
        price=Decimal("110"),
        fee=Decimal("0"),
    )

    position = position_engine.apply(None, fill_processor.accept(buy_fill))
    portfolio = portfolio_engine.apply(portfolio, buy_fill, position)
    position = position_engine.apply(position, fill_processor.accept(sell_fill))
    portfolio = portfolio_engine.apply(portfolio, sell_fill, position)

    assert "btc-usdt" not in portfolio.positions
    assert portfolio.realized_pnl == Decimal("1.0")


def test_fill_processor_rejects_duplicate_fill_identity() -> None:
    fill_processor = IdempotentFillProcessor()
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
    )

    fill_processor.accept(fill)
    with pytest.raises(ValueError):
        fill_processor.accept(fill)


def test_position_engine_rejects_impossible_oversell_fill() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))

    sell_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.SELL,
        quantity=Decimal("0.20"),
        price=Decimal("110"),
        fee=Decimal("0"),
    )

    with pytest.raises(ValueError, match="sell_fill_exceeds_current_position_quantity"):
        position_engine.apply(position, fill_processor.accept(sell_fill))


def test_position_engine_rejects_fill_from_other_instrument_without_mutating_state() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    btc_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
    )
    position = position_engine.apply(None, fill_processor.accept(btc_fill))
    foreign_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=InstrumentRef(instrument_id="eth-usdt", symbol="ETHUSDT", venue="binance"),
        side=OrderSide.BUY,
        quantity=Decimal("0.05"),
        price=Decimal("200"),
    )

    with pytest.raises(ValueError, match="fill_instrument_does_not_match_current_position"):
        position_engine.apply(position, fill_processor.accept(foreign_fill))

    assert position.instrument.instrument_id == "btc-usdt"
    assert position.quantity == Decimal("0.10")


def test_portfolio_engine_marks_impossible_oversell_fill_for_reconcile() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))
    portfolio = portfolio_engine.apply(portfolio, buy_fill, position)

    impossible_sell = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.SELL,
        quantity=Decimal("0.20"),
        price=Decimal("110"),
        fee=Decimal("0"),
    )

    updated_portfolio = portfolio_engine.apply(portfolio, impossible_sell, position)

    assert updated_portfolio.cash_balance == Decimal("1012.0")
    assert updated_portfolio.metadata["reconcile_required"] == "true"
    assert "sell_fill_exceeds_local_position_quantity" in updated_portfolio.metadata["reconcile_reasons"]


def test_impossible_oversell_rejection_leaves_existing_portfolio_truth_unchanged() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    original_portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))
    portfolio = portfolio_engine.apply(original_portfolio, buy_fill, position)

    impossible_sell = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.SELL,
        quantity=Decimal("0.20"),
        price=Decimal("110"),
        fee=Decimal("0"),
    )

    with pytest.raises(ValueError, match="sell_fill_exceeds_current_position_quantity"):
        position_engine.apply(position, fill_processor.accept(impossible_sell))

    assert portfolio.cash_balance == Decimal("990")
    assert portfolio.positions["btc-usdt"].quantity == Decimal("0.10")


def test_portfolio_engine_aggregates_realized_pnl_across_instruments() -> None:
    """realized_pnl must sum across all positions, not just the last one."""
    btc = InstrumentRef(instrument_id="btc-usdt", symbol="BTCUSDT", venue="binance")
    eth = InstrumentRef(instrument_id="eth-usdt", symbol="ETHUSDT", venue="binance")

    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("10000"))

    btc_buy = Fill.create(
        order_intent_id="o1",
        instrument=btc,
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    btc_sell = Fill.create(
        order_intent_id="o2",
        instrument=btc,
        side=OrderSide.SELL,
        quantity=Decimal("1"),
        price=Decimal("110"),
        fee=Decimal("0"),
    )

    btc_pos = position_engine.apply(None, fill_processor.accept(btc_buy))
    portfolio = portfolio_engine.apply(portfolio, btc_buy, btc_pos)
    btc_pos = position_engine.apply(btc_pos, fill_processor.accept(btc_sell))
    portfolio = portfolio_engine.apply(portfolio, btc_sell, btc_pos)

    eth_buy = Fill.create(
        order_intent_id="o3",
        instrument=eth,
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("200"),
        fee=Decimal("0"),
    )
    eth_sell = Fill.create(
        order_intent_id="o4",
        instrument=eth,
        side=OrderSide.SELL,
        quantity=Decimal("1"),
        price=Decimal("205"),
        fee=Decimal("0"),
    )

    eth_pos = position_engine.apply(None, fill_processor.accept(eth_buy))
    portfolio = portfolio_engine.apply(portfolio, eth_buy, eth_pos)
    eth_pos = position_engine.apply(eth_pos, fill_processor.accept(eth_sell))
    portfolio = portfolio_engine.apply(portfolio, eth_sell, eth_pos)

    assert portfolio.realized_pnl == Decimal("15")


def test_portfolio_engine_rejects_resulting_position_instrument_mismatch() -> None:
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
    )
    wrong_position = Position(
        position_id="pos_eth",
        instrument=InstrumentRef(instrument_id="eth-usdt", symbol="ETHUSDT", venue="binance"),
        quantity=Decimal("0.10"),
        average_entry_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        updated_at=portfolio.updated_at,
        metadata={},
    )

    with pytest.raises(ValueError, match="resulting_position_instrument_does_not_match_fill"):
        portfolio_engine.apply(portfolio, fill, wrong_position)


def test_portfolio_engine_rejects_previous_position_instrument_mismatch() -> None:
    portfolio_engine = SpotPortfolioEngine()
    btc = instrument()
    valid_previous = Position(
        position_id="pos_corrupt",
        instrument=btc,
        quantity=Decimal("0.10"),
        average_entry_price=Decimal("100"),
        realized_pnl=Decimal("0"),
        updated_at=utc_now(),
        metadata={},
    )
    portfolio = PortfolioState(
        portfolio_state_id="portfolio_corrupt",
        cash_balance=Decimal("1000"),
        available_cash_balance=Decimal("1000"),
        reserved_cash_balance=Decimal("0"),
        realized_pnl=Decimal("0"),
        equity=Decimal("1000"),
        balances={"cash": Decimal("1000")},
        positions={"btc-usdt": valid_previous},
        updated_at=valid_previous.updated_at,
        metadata={"reconcile_required": "true"},
    )
    object.__setattr__(
        portfolio,
        "positions",
        {
            "btc-usdt": Position(
                position_id="pos_corrupt",
                instrument=InstrumentRef(
                    instrument_id="eth-usdt",
                    symbol="ETHUSDT",
                    venue="binance",
                ),
                quantity=Decimal("0.10"),
                average_entry_price=Decimal("100"),
                realized_pnl=Decimal("0"),
                updated_at=valid_previous.updated_at,
                metadata={},
            )
        },
    )
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=btc,
        side=OrderSide.SELL,
        quantity=Decimal("0.01"),
        price=Decimal("100"),
    )
    next_position = Position.empty(instrument=btc)

    with pytest.raises(ValueError, match="previous_position_instrument_does_not_match_fill"):
        portfolio_engine.apply(portfolio, fill, next_position)


def test_portfolio_state_id_changes_on_each_apply() -> None:
    """Each apply must produce a new portfolio_state_id."""
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))

    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    position = position_engine.apply(None, fill_processor.accept(fill))
    original_id = portfolio.portfolio_state_id
    updated_portfolio = portfolio_engine.apply(portfolio, fill, position)

    assert updated_portfolio.portfolio_state_id != original_id
    assert updated_portfolio.portfolio_state_id.startswith("portfolio_")


def test_fill_processor_rejects_duplicate_external_fill_id_with_different_fill_ids() -> None:
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        external_fill_id="ext_123",
    )
    second = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        external_fill_id="ext_123",
    )

    fill_processor.accept(first)
    with pytest.raises(ValueError):
        fill_processor.accept(second)


def test_fill_processor_rejects_replayed_fill_without_external_id_after_external_accept() -> None:
    fill_processor = IdempotentFillProcessor()
    accepted_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        external_fill_id="ext_123",
    )
    replayed_without_external_id = replace(accepted_fill, external_fill_id=None)

    fill_processor.accept(accepted_fill)
    with pytest.raises(ValueError, match="Duplicate fill_id"):
        fill_processor.accept(replayed_without_external_id)


def test_fill_processor_falls_back_to_internal_fill_id_when_external_id_missing() -> None:
    fill_processor = IdempotentFillProcessor()
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
    )

    fill_processor.accept(fill)
    with pytest.raises(ValueError):
        fill_processor.accept(fill)


def test_fill_processor_rejects_recreated_duplicate_without_external_id() -> None:
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )
    replayed = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )

    fill_processor.accept(first)
    assert fill_processor.accept(replayed) is replayed


def test_fill_processor_accepts_distinct_external_fill_ids() -> None:
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        external_fill_id="ext_123",
    )
    second = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("101"),
        external_fill_id="ext_456",
    )

    assert fill_processor.accept(first) is first
    assert fill_processor.accept(second) is second


def test_fill_processor_accepts_distinct_fallback_fill_identities_without_external_id() -> None:
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
    )
    second = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("101"),
    )

    assert fill_processor.accept(first) is first
    assert fill_processor.accept(second) is second


def test_fill_processor_accepts_partial_fills_with_same_economic_shape_when_lineage_differs() -> None:
    fill_processor = IdempotentFillProcessor()
    first = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
        metadata={"execution_report_id": "exec_1", "execution_fragment": "1"},
    )
    second = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
        metadata={"execution_report_id": "exec_1", "execution_fragment": "2"},
    )

    assert fill_processor.accept(first) is first
    assert fill_processor.accept(second) is second


def test_fill_create_rejects_zero_quantity() -> None:
    with pytest.raises(ValueError):
        Fill.create(
            order_intent_id="ordint_1",
            instrument=instrument(),
            side=OrderSide.BUY,
            quantity=Decimal("0"),
            price=Decimal("100"),
        )


def test_fill_create_rejects_negative_quantity() -> None:
    with pytest.raises(ValueError):
        Fill.create(
            order_intent_id="ordint_1",
            instrument=instrument(),
            side=OrderSide.BUY,
            quantity=Decimal("-1"),
            price=Decimal("100"),
        )


def test_fill_create_rejects_zero_price() -> None:
    with pytest.raises(ValueError):
        Fill.create(
            order_intent_id="ordint_1",
            instrument=instrument(),
            side=OrderSide.BUY,
            quantity=Decimal("0.10"),
            price=Decimal("0"),
        )


def test_fill_create_rejects_negative_price() -> None:
    with pytest.raises(ValueError):
        Fill.create(
            order_intent_id="ordint_1",
            instrument=instrument(),
            side=OrderSide.BUY,
            quantity=Decimal("0.10"),
            price=Decimal("-100"),
        )


def test_fill_create_accepts_zero_fee() -> None:
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("0"),
    )

    assert fill.fee == Decimal("0")


def test_fill_create_accepts_negative_fee_rebate() -> None:
    fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        fee=Decimal("-0.25"),
    )

    assert fill.fee == Decimal("-0.25")


def test_position_updated_at_does_not_go_backward_on_late_fill() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        executed_at=utc_now(),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))
    late_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        price=Decimal("101"),
        executed_at=position.updated_at - timedelta(minutes=5),
    )

    updated_position = position_engine.apply(position, fill_processor.accept(late_fill))

    assert updated_position.updated_at == position.updated_at


def test_portfolio_updated_at_does_not_go_backward_on_late_fill() -> None:
    fill_processor = IdempotentFillProcessor()
    position_engine = SpotPositionEngine()
    portfolio_engine = SpotPortfolioEngine()
    portfolio = PortfolioState.empty(cash_balance=Decimal("1000"))
    buy_fill = Fill.create(
        order_intent_id="ordint_1",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.10"),
        price=Decimal("100"),
        executed_at=utc_now(),
    )
    position = position_engine.apply(None, fill_processor.accept(buy_fill))
    portfolio = portfolio_engine.apply(portfolio, buy_fill, position)
    late_fill = Fill.create(
        order_intent_id="ordint_2",
        instrument=instrument(),
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
        price=Decimal("101"),
        executed_at=portfolio.updated_at - timedelta(minutes=5),
    )
    late_position = position_engine.apply(position, fill_processor.accept(late_fill))

    updated_portfolio = portfolio_engine.apply(portfolio, late_fill, late_position)

    assert updated_portfolio.updated_at == portfolio.updated_at

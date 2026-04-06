from __future__ import annotations

from decimal import Decimal

import pytest

from trading_core.domain import InstrumentRef, InstrumentRiskBasis, OrderSide, PortfolioRiskBasis, RiskVerdict
from trading_core.input import DictEventNormalizer, SimpleMarketContextAssembler
from trading_core.risk import ConfidenceCapRiskEvaluator
from trading_core.strategy import BarDirectionStrategy


def build_intent():
    normalizer = DictEventNormalizer()
    assembler = SimpleMarketContextAssembler(
        entry_timeframe="15m",
        timeframe_set=("15m", "1h"),
        alignment_policy="closed-bars-only",
    )
    strategy = BarDirectionStrategy(min_body_ratio=Decimal("0.001"))
    event = normalizer.normalize(
        {
            "instrument_id": "btc-usdt",
            "symbol": "BTCUSDT",
            "venue": "binance",
            "event_kind": "bar",
            "source": "test-feed",
            "payload": {"timeframe": "15m", "open": "100", "close": "105"},
        }
    )
    context = assembler.assemble(event)
    result = strategy.evaluate(context)
    return result


def build_sell_intent():
    return type(build_intent()).create(
        instrument=InstrumentRef(
            instrument_id="btc-usdt",
            symbol="BTCUSDT",
            venue="binance",
        ),
        side=OrderSide.SELL,
        thesis="position_reduction",
        confidence=Decimal("0.05"),
        strategy_name="test_sell_strategy",
        context_id="ctx_sell_123",
    )


def test_confidence_cap_risk_evaluator_approves_intent() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
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

    assert decision.verdict == RiskVerdict.APPROVED
    assert decision.approved_quantity == Decimal("0.11")


def test_confidence_cap_risk_evaluator_rejects_low_confidence() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.20"))

    decision = evaluator.evaluate(
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

    assert decision.verdict == RiskVerdict.REJECTED
    assert decision.rejection_reason == "confidence_below_threshold"


def test_confidence_cap_risk_evaluator_caps_at_max_quantity() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("0.05"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("105.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.CAPPED
    assert decision.approved_quantity == Decimal("0.05")
    assert decision.rejection_reason == "clamped_to_max_order_quantity"


def test_confidence_cap_risk_evaluator_rejects_non_tradable_instrument() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator()

    decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.01"),
            instrument_tradable=False,
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("105.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.REJECTED
    assert decision.rejection_reason == "instrument_not_tradable"


def test_confidence_cap_risk_evaluator_sizes_in_base_units_using_reference_price() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.0001"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.0001"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("1000.00"),
            max_capital_per_trade=Decimal("1000.00"),
            reference_price=Decimal("65000.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.APPROVED
    assert decision.approved_quantity is not None
    assert decision.approved_quantity == Decimal("0.0007")
    assert decision.approved_quantity < Decimal("1")


def test_confidence_cap_risk_evaluator_aligns_non_power_of_ten_step_with_floor_division() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.05"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.05"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("210.00"),
            max_capital_per_trade=Decimal("210.00"),
            reference_price=Decimal("100.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.APPROVED
    assert decision.approved_quantity == Decimal("0.10")


def test_confidence_cap_risk_evaluator_aligns_thousandth_step_across_reference_prices() -> None:
    intent = build_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    low_price_decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.001"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.001"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("20.00"),
            max_capital_per_trade=Decimal("20.00"),
            reference_price=Decimal("10.00"),
        ),
    )
    high_price_decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.001"),
            max_order_quantity=Decimal("10"),
            quantity_step=Decimal("0.001"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("20.00"),
            max_capital_per_trade=Decimal("20.00"),
            reference_price=Decimal("17.50"),
        ),
    )

    assert low_price_decision.approved_quantity == Decimal("0.100")
    assert high_price_decision.approved_quantity == Decimal("0.057")


def test_confidence_cap_risk_evaluator_rejects_sell_without_position() -> None:
    intent = build_sell_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
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
            current_position_quantity=Decimal("0"),
        ),
    )

    assert decision.verdict == RiskVerdict.REJECTED
    assert decision.rejection_reason == "no_position_to_sell"


def test_confidence_cap_risk_evaluator_rejects_sell_that_exceeds_existing_position() -> None:
    intent = build_sell_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
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
            current_position_quantity=Decimal("0.03"),
        ),
    )

    assert decision.verdict == RiskVerdict.REJECTED
    assert decision.approved_quantity is None
    assert decision.rejection_reason == "sell_quantity_exceeds_position"


def test_confidence_cap_risk_evaluator_still_caps_sell_at_max_order_quantity() -> None:
    intent = build_sell_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
        intent=intent,
        instrument_basis=InstrumentRiskBasis(
            instrument_id="btc-usdt",
            min_order_quantity=Decimal("0.01"),
            max_order_quantity=Decimal("0.05"),
            quantity_step=Decimal("0.01"),
        ),
        portfolio_basis=PortfolioRiskBasis(
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("105.00"),
            current_position_quantity=Decimal("1.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.CAPPED
    assert decision.approved_quantity == Decimal("0.05")
    assert decision.rejection_reason == "clamped_to_max_order_quantity"


def test_confidence_cap_risk_evaluator_approves_sell_when_requested_size_fits_position() -> None:
    intent = build_sell_intent()
    evaluator = ConfidenceCapRiskEvaluator(
        min_confidence=Decimal("0.01"),
        confidence_to_capital_fraction=Decimal("0.1"),
    )

    decision = evaluator.evaluate(
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
            current_position_quantity=Decimal("1.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.APPROVED
    assert decision.approved_quantity == Decimal("0.01")


def test_confidence_cap_risk_evaluator_approves_sell_with_existing_position() -> None:
    intent = build_sell_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
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
            current_position_quantity=Decimal("1.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.APPROVED
    assert decision.approved_quantity == Decimal("0.11")


def test_confidence_cap_risk_evaluator_rejects_sell_when_position_after_cap_is_below_min_order_quantity() -> None:
    intent = build_sell_intent()
    evaluator = ConfidenceCapRiskEvaluator(min_confidence=Decimal("0.01"))

    decision = evaluator.evaluate(
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
            current_position_quantity=Decimal("0.005"),
        ),
    )

    assert decision.verdict == RiskVerdict.REJECTED
    assert decision.rejection_reason == "sell_quantity_exceeds_position"


def test_confidence_cap_risk_evaluator_rejects_non_positive_reference_price() -> None:
    with pytest.raises(ValueError, match="reference_price_must_be_positive"):
        PortfolioRiskBasis(
            available_capital=Decimal("500.00"),
            max_capital_per_trade=Decimal("250.00"),
            reference_price=Decimal("0"),
        )

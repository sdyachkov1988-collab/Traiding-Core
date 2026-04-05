from __future__ import annotations

from decimal import Decimal

from trading_core.domain import InstrumentRiskBasis, PortfolioRiskBasis, RiskVerdict
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
            available_capital=Decimal("5.00"),
            max_capital_per_trade=Decimal("2.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.APPROVED
    assert decision.approved_quantity == Decimal("0.10")


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
            available_capital=Decimal("5.00"),
            max_capital_per_trade=Decimal("2.00"),
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
            available_capital=Decimal("5.00"),
            max_capital_per_trade=Decimal("2.00"),
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
            available_capital=Decimal("5.00"),
            max_capital_per_trade=Decimal("2.00"),
        ),
    )

    assert decision.verdict == RiskVerdict.REJECTED
    assert decision.rejection_reason == "instrument_not_tradable"

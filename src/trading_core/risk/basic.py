"""Reference risk evaluator implementations for Package C."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from trading_core.domain.risk import (
    InstrumentRiskBasis,
    PortfolioRiskBasis,
    RiskDecision,
    RiskVerdict,
)
from trading_core.domain.strategy import StrategyIntent


@dataclass(slots=True)
class ConfidenceCapRiskEvaluator:
    """A minimal risk evaluator using confidence and portfolio caps."""

    min_confidence: Decimal = Decimal("0.01")
    confidence_to_capital_fraction: Decimal = Decimal("1.0")

    def evaluate(
        self,
        intent: StrategyIntent,
        instrument_basis: InstrumentRiskBasis,
        portfolio_basis: PortfolioRiskBasis,
    ) -> RiskDecision:
        """Return a separate risk verdict without mutating downstream state."""

        if not instrument_basis.instrument_tradable:
            return RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="instrument_not_tradable",
                metadata={"instrument_id": instrument_basis.instrument_id},
            )

        if not portfolio_basis.portfolio_tradable:
            return RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="portfolio_not_tradable",
                metadata={"instrument_id": instrument_basis.instrument_id},
            )

        if intent.confidence < self.min_confidence:
            return RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="confidence_below_threshold",
                metadata={"instrument_id": instrument_basis.instrument_id},
            )

        allowed_capital = min(
            portfolio_basis.available_capital,
            portfolio_basis.max_capital_per_trade,
        )
        scaled_capital = allowed_capital * min(
            Decimal("1.0"),
            intent.confidence * self.confidence_to_capital_fraction,
        )
        raw_quantity = scaled_capital.quantize(instrument_basis.quantity_step, rounding=ROUND_DOWN)

        if raw_quantity < instrument_basis.min_order_quantity:
            return RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="below_min_order_quantity",
                metadata={"instrument_id": instrument_basis.instrument_id},
            )

        approved_quantity = min(raw_quantity, instrument_basis.max_order_quantity)
        if approved_quantity < raw_quantity:
            return RiskDecision.create(
                verdict=RiskVerdict.CAPPED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                approved_quantity=approved_quantity,
                rejection_reason="clamped_to_max_order_quantity",
                metadata={"instrument_id": instrument_basis.instrument_id},
            )

        return RiskDecision.create(
            verdict=RiskVerdict.APPROVED,
            strategy_intent_id=intent.intent_id,
            instrument=intent.instrument,
            side=intent.side,
            approved_quantity=approved_quantity,
            metadata={"instrument_id": instrument_basis.instrument_id},
        )

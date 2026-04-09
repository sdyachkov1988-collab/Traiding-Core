"""Reference risk evaluator implementations for Package C."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.orders import OrderSide
from trading_core.domain.risk import (
    InstrumentRiskBasis,
    PortfolioRiskBasis,
    RiskDecision,
    RiskVerdict,
)
from trading_core.domain.strategy import StrategyIntent
from trading_core.observability import emit_structured_event


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

        if intent.instrument.instrument_id != instrument_basis.instrument_id:
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="instrument_basis_mismatch",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )
        if not instrument_basis.instrument_tradable:
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="instrument_not_tradable",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )

        if not portfolio_basis.portfolio_tradable:
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="portfolio_not_tradable",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )

        if intent.confidence < self.min_confidence:
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="confidence_below_threshold",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )

        if portfolio_basis.reference_price <= Decimal("0"):
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="reference_price_not_positive",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )

        allowed_capital = min(
            portfolio_basis.available_capital,
            portfolio_basis.max_capital_per_trade,
        )
        scaled_capital = allowed_capital * min(
            Decimal("1.0"),
            intent.confidence * self.confidence_to_capital_fraction,
        )
        approved_quantity = scaled_capital / portfolio_basis.reference_price
        raw_quantity = (
            approved_quantity // instrument_basis.quantity_step
        ) * instrument_basis.quantity_step

        if intent.side is OrderSide.SELL:
            if portfolio_basis.current_position_quantity <= Decimal("0"):
                return self._log_decision(
                    RiskDecision.create(
                    verdict=RiskVerdict.REJECTED,
                    strategy_intent_id=intent.intent_id,
                    instrument=intent.instrument,
                    side=intent.side,
                    rejection_reason="no_position_to_sell",
                    metadata={"instrument_id": instrument_basis.instrument_id},
                    )
                )
            if raw_quantity > portfolio_basis.current_position_quantity:
                return self._log_decision(
                    RiskDecision.create(
                    verdict=RiskVerdict.REJECTED,
                    strategy_intent_id=intent.intent_id,
                    instrument=intent.instrument,
                    side=intent.side,
                    rejection_reason="sell_quantity_exceeds_position",
                    metadata={
                        "instrument_id": instrument_basis.instrument_id,
                        "requested_quantity": str(raw_quantity),
                        "current_position_quantity": str(
                            portfolio_basis.current_position_quantity
                        ),
                    },
                    )
                )

        if raw_quantity < instrument_basis.min_order_quantity:
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.REJECTED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                rejection_reason="below_min_order_quantity",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )

        if raw_quantity > instrument_basis.max_order_quantity:
            return self._log_decision(
                RiskDecision.create(
                verdict=RiskVerdict.CAPPED,
                strategy_intent_id=intent.intent_id,
                instrument=intent.instrument,
                side=intent.side,
                approved_quantity=instrument_basis.max_order_quantity,
                rejection_reason="clamped_to_max_order_quantity",
                metadata={"instrument_id": instrument_basis.instrument_id},
                )
            )

        return self._log_decision(
            RiskDecision.create(
            verdict=RiskVerdict.APPROVED,
            strategy_intent_id=intent.intent_id,
            instrument=intent.instrument,
            side=intent.side,
            approved_quantity=raw_quantity,
            metadata={"instrument_id": instrument_basis.instrument_id},
            )
        )

    def _log_decision(self, decision: RiskDecision) -> RiskDecision:
        emit_structured_event(
            logger_name=__name__,
            event_type="risk_decision",
            entity_type="risk_decision",
            entity_id=decision.risk_decision_id,
            lineage_id=decision.strategy_intent_id,
            stage="risk",
            lifecycle_step="decision_emitted",
            decision=decision.verdict.value,
            outcome=decision.verdict.value,
            reason=decision.rejection_reason,
            reason_code=decision.rejection_reason,
            metadata={"instrument_id": decision.instrument.instrument_id},
        )
        return decision

"""Contracts for Package C seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.risk import InstrumentRiskBasis, PortfolioRiskBasis, RiskDecision
from trading_core.domain.strategy import StrategyIntent


class RiskEvaluator(Protocol):
    """Produce a separate downstream risk verdict."""

    def evaluate(
        self,
        intent: StrategyIntent,
        instrument_basis: InstrumentRiskBasis,
        portfolio_basis: PortfolioRiskBasis,
    ) -> RiskDecision:
        """Return the risk verdict for the upstream strategy intent."""

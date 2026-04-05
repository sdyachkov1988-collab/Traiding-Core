"""Contracts for early order construction seams."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.instruments import ExecutionConstraintBasis, InstrumentExecutionSpec
from trading_core.domain.orders import OrderIntent
from trading_core.domain.risk import RiskDecision


class OrderIntentBuilder(Protocol):
    """Build executable order intent from a risk-approved decision."""

    def build(
        self,
        decision: RiskDecision,
        instrument_spec: InstrumentExecutionSpec,
        execution_basis: ExecutionConstraintBasis,
    ) -> OrderIntent:
        """Return an order intent that is executable at the core boundary."""

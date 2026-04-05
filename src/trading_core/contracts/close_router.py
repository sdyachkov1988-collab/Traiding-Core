"""Contracts for Wave 2E close-routing seam."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from trading_core.domain.close_intent import CloseIntent, CloseRoutingResult
from trading_core.domain.guards import ExecutionAdmissibilityBasis
from trading_core.domain.instruments import ExecutionConstraintBasis, InstrumentExecutionSpec


@runtime_checkable
class CloseIntentRouterProtocol(Protocol):
    """Route a position-originated close intent through builder and guard seams."""

    def route(
        self,
        close_intent: CloseIntent,
        instrument_spec: InstrumentExecutionSpec,
        execution_basis: ExecutionConstraintBasis,
        admissibility_basis: ExecutionAdmissibilityBasis,
    ) -> CloseRoutingResult:
        """Return an explicit routing result for the close intent."""

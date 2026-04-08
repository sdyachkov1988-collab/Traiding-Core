"""Active runtime contour for the mature Wave 2 strategy cycle."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.contracts.context import TimeframeContextProvider
from trading_core.contracts.coordinator import RecoveryCoordinatorProtocol
from trading_core.contracts.gate import ContextGateProtocol
from trading_core.contracts.recovery import UnknownStateClassifierProtocol
from trading_core.contracts.strategy import Strategy, StrategyResult
from trading_core.domain.gate import GateOutcome, GateVerdict
from trading_core.domain.reconciliation_extended import ReconciliationOutcome, ReconciliationRequest
from trading_core.domain.timeframe import TimeframeContext
from trading_core.domain.unknown import SystemModeTransition


@dataclass(frozen=True, slots=True)
class RuntimeCycleResult:
    """Result of one active runtime strategy cycle."""

    context: TimeframeContext | None = None
    gate_outcome: GateOutcome | None = None
    strategy_result: StrategyResult | None = None
    blocked_by_system_posture: bool = False


@dataclass(slots=True)
class ActiveRuntimeContour:
    """Wire mature Wave 2 context, gate, strategy, posture, and reconciliation seams."""

    context_provider: TimeframeContextProvider
    gate: ContextGateProtocol
    strategy: Strategy
    classifier: UnknownStateClassifierProtocol
    recovery_coordinator: RecoveryCoordinatorProtocol

    def run_cycle(self) -> RuntimeCycleResult:
        """Run one strategy cycle through posture check, context assembly, gate, and strategy."""

        if not self.classifier.is_trading_allowed():
            return RuntimeCycleResult(blocked_by_system_posture=True)

        context = self.context_provider.assemble()
        gate_outcome = self.gate.check(context)
        if gate_outcome.verdict is not GateVerdict.ADMITTED:
            return RuntimeCycleResult(
                context=context,
                gate_outcome=gate_outcome,
            )

        if context is None:
            raise AssertionError("admitted_gate_outcome_requires_context")

        return RuntimeCycleResult(
            context=context,
            gate_outcome=gate_outcome,
            strategy_result=self.strategy.evaluate(context),
        )

    def request_startup_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Expose startup reconciliation as a runtime capability."""

        return self.recovery_coordinator.request_startup_reconciliation(instrument_id)

    def request_periodic_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Expose periodic reconciliation as a runtime capability."""

        return self.recovery_coordinator.request_periodic_reconciliation(instrument_id)

    def request_on_error_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Expose on-error reconciliation as a runtime capability."""

        return self.recovery_coordinator.request_on_error_reconciliation(instrument_id)

    def request_operator_reconciliation(
        self,
        instrument_id: str | None = None,
    ) -> ReconciliationRequest:
        """Expose operator-command reconciliation as a runtime capability."""

        return self.recovery_coordinator.request_operator_reconciliation(instrument_id)

    def process_reconciliation_outcome(
        self,
        outcome: ReconciliationOutcome,
    ) -> SystemModeTransition | None:
        """Delegate reconciliation outcome handling to the runtime recovery capability."""

        return self.recovery_coordinator.process_outcome(outcome)

"""Domain layer for canonical trading entities."""

from trading_core.domain.common import InstrumentRef
from trading_core.domain.close_intent import CloseIntent, CloseRoutingResult, CloseRoutingVerdict
from trading_core.domain.context import MarketContext, Wave1MtfContext
from trading_core.domain.execution import AdmittedOrder, ExecutionReport, ExecutionReportKind
from trading_core.domain.events import EventKind, MarketEvent
from trading_core.domain.fills import Fill
from trading_core.domain.gate import GateOutcome, GateVerdict
from trading_core.domain.guards import ExecutionAdmissibilityBasis, GuardOutcome, GuardVerdict
from trading_core.domain.instruments import ExecutionConstraintBasis, InstrumentExecutionSpec
from trading_core.domain.orders import OrderIntent, OrderSide, OrderType, TimeInForce
from trading_core.domain.portfolio_state import PortfolioState, Position
from trading_core.domain.reconciliation import (
    ExternalStartupBasis,
    ExternalStartupPosition,
    StartupReconciliationResult,
    StartupReconciliationVerdict,
)
from trading_core.domain.reconciliation_extended import (
    ReconciliationMode,
    ReconciliationOutcome,
    ReconciliationRequest,
    ReconciliationTrigger,
    ReconciliationVerdict,
)
from trading_core.domain.risk import (
    InstrumentRiskBasis,
    PortfolioRiskBasis,
    RiskDecision,
    RiskVerdict,
)
from trading_core.domain.state import PersistedOrderRecord, PersistedStateSnapshot
from trading_core.domain.strategy import NoAction, StrategyIntent
from trading_core.domain.timeframe import ClosedBar, TimeframeContext, TimeframeSyncEvent
from trading_core.domain.unknown import (
    SystemMode,
    SystemModeTransition,
    UnknownStateKind,
    UnknownStateRecord,
)

__all__ = [
    "AdmittedOrder",
    "ClosedBar",
    "CloseIntent",
    "CloseRoutingResult",
    "CloseRoutingVerdict",
    "EventKind",
    "ExecutionReport",
    "ExecutionAdmissibilityBasis",
    "ExecutionConstraintBasis",
    "ExecutionReportKind",
    "ExternalStartupBasis",
    "ExternalStartupPosition",
    "Fill",
    "GateOutcome",
    "GateVerdict",
    "GuardOutcome",
    "GuardVerdict",
    "InstrumentRef",
    "InstrumentRiskBasis",
    "InstrumentExecutionSpec",
    "MarketContext",
    "MarketEvent",
    "NoAction",
    "OrderIntent",
    "OrderSide",
    "OrderType",
    "PortfolioState",
    "PortfolioRiskBasis",
    "PersistedOrderRecord",
    "PersistedStateSnapshot",
    "Position",
    "ReconciliationMode",
    "ReconciliationOutcome",
    "ReconciliationRequest",
    "ReconciliationTrigger",
    "ReconciliationVerdict",
    "RiskDecision",
    "RiskVerdict",
    "StartupReconciliationResult",
    "StartupReconciliationVerdict",
    "StrategyIntent",
    "SystemMode",
    "SystemModeTransition",
    "TimeInForce",
    "TimeframeContext",
    "TimeframeSyncEvent",
    "UnknownStateKind",
    "UnknownStateRecord",
    "Wave1MtfContext",
]

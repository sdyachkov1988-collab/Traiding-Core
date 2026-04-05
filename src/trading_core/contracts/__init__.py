"""Interface contracts for Minimal Core v1 seams."""

from trading_core.contracts.context import TimeframeContextProvider
from trading_core.contracts.execution import ExecutionAdapter
from trading_core.contracts.fills import FillProcessor, PortfolioEngine, PositionEngine
from trading_core.contracts.gate import ContextGateProtocol
from trading_core.contracts.guards import PreExecutionGuard
from trading_core.contracts.input import EventNormalizer, MarketContextAssembler
from trading_core.contracts.orders import OrderIntentBuilder
from trading_core.contracts.reconciliation import StartupReconciler
from trading_core.contracts.recovery import UnknownStateClassifierProtocol
from trading_core.contracts.risk import RiskEvaluator
from trading_core.contracts.strategy import Strategy
from trading_core.contracts.state import StateStore

__all__ = [
    "ContextGateProtocol",
    "ExecutionAdapter",
    "EventNormalizer",
    "FillProcessor",
    "MarketContextAssembler",
    "OrderIntentBuilder",
    "PortfolioEngine",
    "PreExecutionGuard",
    "PositionEngine",
    "RiskEvaluator",
    "StartupReconciler",
    "StateStore",
    "Strategy",
    "TimeframeContextProvider",
    "UnknownStateClassifierProtocol",
]

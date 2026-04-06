"""Execution boundary and execution-facing seams."""

from trading_core.execution.adapters import MockExecutionAdapter
from trading_core.execution.builders import SimpleOrderIntentBuilder
from trading_core.execution.fills import IdempotentFillProcessor
from trading_core.execution.guards import SimplePreExecutionGuard
from trading_core.execution.handoff import ExecutionHandoff

__all__ = [
    "IdempotentFillProcessor",
    "ExecutionHandoff",
    "MockExecutionAdapter",
    "SimpleOrderIntentBuilder",
    "SimplePreExecutionGuard",
]

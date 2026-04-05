"""Contracts for Package E execution boundary."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.execution import AdmittedOrder, ExecutionReport


class ExecutionAdapter(Protocol):
    """Single boundary between the core and external execution."""

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Submit an admitted order and return only normalized execution reports."""

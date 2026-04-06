"""Contracts for Package E execution boundary."""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping
from typing import Protocol, runtime_checkable

from trading_core.domain.execution import AdmittedOrder, ExecutionReport
from trading_core.domain.instruments import InstrumentExecutionSpec


@runtime_checkable
class ExecutionSubmitter(Protocol):
    """Submit admitted orders through the normalized execution boundary."""

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Submit an admitted order and return only normalized execution reports."""


@runtime_checkable
class ExecutionAdapter(Protocol):
    """Single boundary between the core and external execution."""

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Submit an admitted order and return only normalized execution reports."""

    def cancel(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Cancel an external order and return normalized execution updates."""

    def query(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Query the latest normalized execution-side picture for an order."""

    def get_balances(self) -> Mapping[str, Decimal]:
        """Return a normalized account-balance view without vendor-specific payloads."""

    def get_instrument_spec(self, instrument_id: str) -> InstrumentExecutionSpec:
        """Return normalized execution constraints for a specific instrument."""

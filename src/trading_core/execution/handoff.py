"""Minimal execution handoff service for the expanded Package E boundary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from trading_core.contracts.execution import ExecutionAdapter
from trading_core.domain.execution import AdmittedOrder, ExecutionReport
from trading_core.domain.instruments import InstrumentExecutionSpec


@dataclass(slots=True)
class ExecutionHandoff:
    """Thin orchestration wrapper over the normalized execution boundary."""

    adapter: ExecutionAdapter

    def place(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Place an admitted order through the execution boundary."""

        return self.adapter.submit(admitted_order)

    def cancel(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Cancel an order through the execution boundary."""

        return self.adapter.cancel(external_order_id)

    def query(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Query order state through the execution boundary."""

        return self.adapter.query(external_order_id)

    def get_balances(self) -> Mapping[str, Decimal]:
        """Expose normalized account balances from the execution boundary."""

        return self.adapter.get_balances()

    def get_instrument_spec(self, instrument_id: str) -> InstrumentExecutionSpec:
        """Expose normalized execution constraints for one instrument."""

        return self.adapter.get_instrument_spec(instrument_id)

"""Reference execution adapters for Package E."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Mapping

from trading_core.domain.execution import AdmittedOrder, ExecutionReport, ExecutionReportKind
from trading_core.domain.instruments import InstrumentExecutionSpec


@dataclass(slots=True)
class MockExecutionAdapter:
    """Mock execution boundary returning normalized execution-side updates."""

    accept_orders: bool = True
    broker_prefix: str = "mock"
    simulate_timeout_on_submit: bool = False
    simulate_missing_confirmation: bool = False
    duplicate_acknowledgement: bool = False
    balances: Mapping[str, Decimal] = field(default_factory=dict)
    instrument_specs: Mapping[str, InstrumentExecutionSpec] = field(default_factory=dict)
    _order_reports: dict[str, tuple[ExecutionReport, ...]] = field(
        default_factory=dict,
        init=False,
    )
    _order_ids_by_external_id: dict[str, str] = field(default_factory=dict, init=False)

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Return normalized execution reports without doing fill accounting."""

        submitted = ExecutionReport.create(
            kind=ExecutionReportKind.SUBMITTED,
            order_intent_id=admitted_order.order_intent.order_intent_id,
            metadata={"admitted_order_id": admitted_order.admitted_order_id},
        )
        if self.simulate_timeout_on_submit:
            timeout_report = ExecutionReport.create(
                kind=ExecutionReportKind.TIMEOUT,
                order_intent_id=admitted_order.order_intent.order_intent_id,
                reason="adapter_submission_timeout",
                metadata={"admitted_order_id": admitted_order.admitted_order_id},
            )
            return (submitted, timeout_report)
        if not self.accept_orders:
            rejected = ExecutionReport.create(
                kind=ExecutionReportKind.REJECTED,
                order_intent_id=admitted_order.order_intent.order_intent_id,
                reason="adapter_rejected_submission",
                metadata={"admitted_order_id": admitted_order.admitted_order_id},
            )
            return (submitted, rejected)

        external_order_id = (
            f"{self.broker_prefix}_{admitted_order.order_intent.order_intent_id}"
        )
        accepted = ExecutionReport.create(
            kind=ExecutionReportKind.ACCEPTED,
            order_intent_id=admitted_order.order_intent.order_intent_id,
            external_order_id=external_order_id,
            metadata={"admitted_order_id": admitted_order.admitted_order_id},
        )
        if self.simulate_missing_confirmation:
            pending = ExecutionReport.create(
                kind=ExecutionReportKind.PENDING,
                order_intent_id=admitted_order.order_intent.order_intent_id,
                external_order_id=external_order_id,
                reason="missing_execution_confirmation",
                metadata={"admitted_order_id": admitted_order.admitted_order_id},
            )
            reports = (submitted, accepted, pending)
            self._order_reports[external_order_id] = reports
            self._order_ids_by_external_id[external_order_id] = (
                admitted_order.order_intent.order_intent_id
            )
            return reports
        acknowledged = ExecutionReport.create(
            kind=ExecutionReportKind.ACKNOWLEDGED,
            order_intent_id=admitted_order.order_intent.order_intent_id,
            external_order_id=external_order_id,
            metadata={"admitted_order_id": admitted_order.admitted_order_id},
        )
        reports = (submitted, accepted, acknowledged)
        if self.duplicate_acknowledgement:
            reports = (
                *reports,
                ExecutionReport.create(
                    kind=ExecutionReportKind.ACKNOWLEDGED,
                    order_intent_id=admitted_order.order_intent.order_intent_id,
                    external_order_id=external_order_id,
                    reason="duplicate_acknowledgement",
                    metadata={"admitted_order_id": admitted_order.admitted_order_id},
                ),
            )
        self._order_reports[external_order_id] = reports
        self._order_ids_by_external_id[external_order_id] = (
            admitted_order.order_intent.order_intent_id
        )
        return reports

    def cancel(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Return a normalized cancellation report for a known external order."""

        order_intent_id = self._order_ids_by_external_id.get(external_order_id)
        if order_intent_id is None:
            return (
                ExecutionReport.create(
                    kind=ExecutionReportKind.REJECTED,
                    order_intent_id="unknown_order_intent",
                    external_order_id=external_order_id,
                    reason="unknown_external_order_id",
                ),
            )

        cancelled = ExecutionReport.create(
            kind=ExecutionReportKind.CANCELLED,
            order_intent_id=order_intent_id,
            external_order_id=external_order_id,
        )
        self._order_reports[external_order_id] = (
            *self._order_reports.get(external_order_id, ()),
            cancelled,
        )
        return (cancelled,)

    def query(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Return the normalized report history for a known external order."""

        if external_order_id not in self._order_reports:
            return (
                ExecutionReport.create(
                    kind=ExecutionReportKind.REJECTED,
                    order_intent_id="unknown_order_intent",
                    external_order_id=external_order_id,
                    reason="unknown_external_order_id",
                ),
            )
        return self._order_reports[external_order_id]

    def get_balances(self) -> Mapping[str, Decimal]:
        """Return the normalized mock balance picture."""

        return dict(self.balances)

    def get_instrument_spec(self, instrument_id: str) -> InstrumentExecutionSpec:
        """Return the normalized execution spec configured for the mock adapter."""

        try:
            return self.instrument_specs[instrument_id]
        except KeyError as exc:
            raise ValueError(f"unknown_instrument_spec:{instrument_id}") from exc

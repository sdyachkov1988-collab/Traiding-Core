"""Reference execution adapters for Package E."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.domain.execution import AdmittedOrder, ExecutionReport, ExecutionReportKind


@dataclass(slots=True)
class MockExecutionAdapter:
    """Mock execution boundary returning normalized execution-side updates."""

    accept_orders: bool = True
    broker_prefix: str = "mock"

    def submit(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Return normalized execution reports without doing fill accounting."""

        submitted = ExecutionReport.create(
            kind=ExecutionReportKind.SUBMITTED,
            order_intent_id=admitted_order.order_intent.order_intent_id,
            metadata={"admitted_order_id": admitted_order.admitted_order_id},
        )
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
        acknowledged = ExecutionReport.create(
            kind=ExecutionReportKind.ACKNOWLEDGED,
            order_intent_id=admitted_order.order_intent.order_intent_id,
            external_order_id=external_order_id,
            metadata={"admitted_order_id": admitted_order.admitted_order_id},
        )
        return (submitted, accepted, acknowledged)

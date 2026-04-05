"""Reference execution adapters for Package E."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from trading_core.domain.execution import AdmittedOrder, ExecutionReport, ExecutionReportKind
from trading_core.domain.fills import Fill


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

    def materialize_fill(
        self,
        admitted_order: AdmittedOrder,
        report: ExecutionReport,
        *,
        execution_price: Decimal | None = None,
        fee: Decimal = Decimal("0"),
    ) -> Fill:
        """Create a normalized fill fact from an accepted execution report."""

        if report.kind not in (ExecutionReportKind.ACCEPTED, ExecutionReportKind.ACKNOWLEDGED):
            raise ValueError("Fill materialization requires an accepted or acknowledged report")
        if report.order_intent_id != admitted_order.order_intent.order_intent_id:
            raise ValueError("ExecutionReport does not match AdmittedOrder")
        resolved_execution_price = admitted_order.order_intent.limit_price
        if resolved_execution_price is None:
            resolved_execution_price = execution_price
        if resolved_execution_price is None:
            raise ValueError(
                "MockExecutionAdapter requires explicit execution_price for non-limit fill materialization"
            )

        return Fill.create(
            order_intent_id=admitted_order.order_intent.order_intent_id,
            instrument=admitted_order.order_intent.instrument,
            side=admitted_order.order_intent.side,
            quantity=admitted_order.order_intent.quantity,
            price=resolved_execution_price,
            fee=fee,
            external_fill_id=report.external_order_id,
            metadata={
                "admitted_order_id": admitted_order.admitted_order_id,
                "execution_report_id": report.report_id,
                "execution_price_source": (
                    "order_limit_price"
                    if admitted_order.order_intent.limit_price is not None
                    else "explicit_execution_price"
                ),
            },
        )

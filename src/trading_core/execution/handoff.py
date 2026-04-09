"""Minimal execution handoff service for the expanded Package E boundary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

from trading_core.contracts.execution import ExecutionAdapter
from trading_core.domain.execution import AdmittedOrder, ExecutionReport
from trading_core.domain.execution import ExecutionReportKind
from trading_core.domain.fills import Fill
from trading_core.domain.instruments import InstrumentExecutionSpec
from trading_core.observability import emit_structured_event


@dataclass(slots=True)
class ExecutionHandoff:
    """Thin orchestration wrapper over the normalized execution boundary."""

    adapter: ExecutionAdapter

    def place(self, admitted_order: AdmittedOrder) -> tuple[ExecutionReport, ...]:
        """Place an admitted order through the execution boundary."""

        reports = self.adapter.submit(admitted_order)
        for report in reports:
            self._log_report(report)
        return reports

    def cancel(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Cancel an order through the execution boundary."""

        reports = self.adapter.cancel(external_order_id)
        for report in reports:
            self._log_report(report)
        return reports

    def query(self, external_order_id: str) -> tuple[ExecutionReport, ...]:
        """Query order state through the execution boundary."""

        reports = self.adapter.query(external_order_id)
        for report in reports:
            self._log_report(report)
        return reports

    def get_balances(self) -> Mapping[str, Decimal]:
        """Expose normalized account balances from the execution boundary."""

        return self.adapter.get_balances()

    def get_instrument_spec(self, instrument_id: str) -> InstrumentExecutionSpec:
        """Expose normalized execution constraints for one instrument."""

        return self.adapter.get_instrument_spec(instrument_id)

    def materialize_fill(
        self,
        admitted_order: AdmittedOrder,
        report: ExecutionReport,
        *,
        execution_price: Decimal | None = None,
        fee: Decimal = Decimal("0"),
    ) -> Fill:
        """Normalize one accepted execution-side report into a fill fact."""

        self._validate_fill_handoff(admitted_order, report)
        resolved_execution_price = self._resolve_execution_price(
            admitted_order=admitted_order,
            execution_price=execution_price,
        )
        fill = Fill.create(
            order_intent_id=admitted_order.order_intent.order_intent_id,
            instrument=admitted_order.order_intent.instrument,
            side=admitted_order.order_intent.side,
            quantity=admitted_order.order_intent.quantity,
            price=resolved_execution_price,
            fee=fee,
            external_fill_id=self._external_fill_id(report, fragment=None),
            executed_at=report.observed_at,
            metadata={
                "admitted_order_id": admitted_order.admitted_order_id,
                "execution_report_id": report.report_id,
                "external_order_id": report.external_order_id or "",
                "execution_price_source": (
                    "order_limit_price"
                    if admitted_order.order_intent.limit_price is not None
                    else "explicit_execution_price"
                ),
            },
        )
        self._log_fill(fill)
        return fill

    def materialize_fills(
        self,
        admitted_order: AdmittedOrder,
        report: ExecutionReport,
        *,
        quantities: tuple[Decimal, ...] | None = None,
        execution_price: Decimal | None = None,
        fees: tuple[Decimal, ...] | None = None,
    ) -> tuple[Fill, ...]:
        """Normalize one execution-side report into one or more downstream fill facts."""

        self._validate_fill_handoff(admitted_order, report)
        fill_quantities = quantities or (admitted_order.order_intent.quantity,)
        total_quantity = sum(fill_quantities, start=Decimal("0"))
        if total_quantity > admitted_order.order_intent.quantity:
            raise ValueError("partial_fill_plan_exceeds_order_quantity")

        materialized_fees = fees or tuple(Decimal("0") for _ in fill_quantities)
        if len(materialized_fees) != len(fill_quantities):
            raise ValueError("fees_length_must_match_partial_fill_plan")

        if len(fill_quantities) == 1:
            return (
                self.materialize_fill(
                    admitted_order,
                    report,
                    execution_price=execution_price,
                    fee=materialized_fees[0],
                ),
            )

        resolved_execution_price = self._resolve_execution_price(
            admitted_order=admitted_order,
            execution_price=execution_price,
        )
        fills: list[Fill] = []
        for index, (quantity, fee) in enumerate(zip(fill_quantities, materialized_fees), start=1):
            fills.append(
                Fill.create(
                    order_intent_id=admitted_order.order_intent.order_intent_id,
                    instrument=admitted_order.order_intent.instrument,
                    side=admitted_order.order_intent.side,
                    quantity=quantity,
                    price=resolved_execution_price,
                    fee=fee,
                    external_fill_id=self._external_fill_id(report, fragment=index),
                    executed_at=report.observed_at,
                    metadata={
                        "admitted_order_id": admitted_order.admitted_order_id,
                        "execution_report_id": report.report_id,
                        "execution_fragment": str(index),
                        "external_order_id": report.external_order_id or "",
                        "execution_price_source": (
                            "order_limit_price"
                            if admitted_order.order_intent.limit_price is not None
                            else "explicit_execution_price"
                        ),
                    },
                )
            )
        for fill in fills:
            self._log_fill(fill)
        return tuple(fills)

    def _validate_fill_handoff(
        self,
        admitted_order: AdmittedOrder,
        report: ExecutionReport,
    ) -> None:
        if report.kind not in (ExecutionReportKind.ACCEPTED, ExecutionReportKind.ACKNOWLEDGED):
            raise ValueError("Fill materialization requires an accepted or acknowledged report")
        if report.order_intent_id != admitted_order.order_intent.order_intent_id:
            raise ValueError("ExecutionReport does not match AdmittedOrder")

    def _resolve_execution_price(
        self,
        *,
        admitted_order: AdmittedOrder,
        execution_price: Decimal | None,
    ) -> Decimal:
        resolved_execution_price = admitted_order.order_intent.limit_price or execution_price
        if resolved_execution_price is None:
            raise ValueError(
                "ExecutionHandoff requires explicit execution_price for non-limit fill materialization"
            )
        return resolved_execution_price

    def _external_fill_id(self, report: ExecutionReport, *, fragment: int | None) -> str:
        base_order_id = report.external_order_id or "execution_report"
        fragment_suffix = "" if fragment is None else f"_{fragment}"
        return f"{base_order_id}_fill_{report.report_id}{fragment_suffix}"

    def _log_report(self, report: ExecutionReport) -> None:
        emit_structured_event(
            logger_name=__name__,
            event_type="execution_report",
            entity_type="execution_report",
            entity_id=report.report_id,
            lineage_id=report.order_intent_id,
            stage="execution_boundary",
            lifecycle_step="report_received",
            decision=report.kind.value,
            outcome=report.kind.value,
            reason=report.reason,
            reason_code=report.reason,
            metadata={
                "external_order_id": report.external_order_id or "",
            },
        )

    def _log_fill(self, fill: Fill) -> None:
        emit_structured_event(
            logger_name=__name__,
            event_type="fill_fact",
            entity_type="fill",
            entity_id=fill.fill_id,
            lineage_id=fill.order_intent_id,
            stage="fill_processing",
            lifecycle_step="fill_materialized",
            decision="materialize_fill",
            outcome="created",
            reason=fill.metadata.get("execution_report_id"),
            reason_code=fill.metadata.get("execution_report_id"),
            metadata={
                "instrument_id": fill.instrument.instrument_id,
                "external_fill_id": fill.external_fill_id or "",
            },
        )

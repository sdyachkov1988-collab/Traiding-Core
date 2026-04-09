"""Fill intake for the first internal truth spine."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from trading_core.domain.fills import Fill
from trading_core.domain.state import FillDedupCheckpoint
from trading_core.observability import emit_structured_event


@dataclass(slots=True)
class IdempotentFillProcessor:
    """Accept fill facts once and expose them to the downstream spine."""

    _seen_external_ids: set[str] = field(default_factory=set)
    _seen_fill_ids: set[str] = field(default_factory=set)
    _seen_fallback_keys: set[tuple[str, ...]] = field(default_factory=set)

    def restore_processed_fill_id(self, fill_id: str | None) -> None:
        """Seed the processor with the latest persisted internal fill identity."""

        if fill_id is None:
            return
        self._seen_fill_ids.add(fill_id)

    def checkpoint(self) -> FillDedupCheckpoint:
        """Return an explicit dedup checkpoint suitable for persistence."""

        return FillDedupCheckpoint(
            seen_fill_ids=tuple(sorted(self._seen_fill_ids)),
            seen_external_fill_ids=tuple(sorted(self._seen_external_ids)),
            seen_fallback_keys=tuple(sorted(self._seen_fallback_keys)),
        )

    def restore_checkpoint(self, checkpoint: FillDedupCheckpoint | None) -> None:
        """Restore dedup state from a persisted checkpoint."""

        if checkpoint is None:
            return
        self._seen_fill_ids.update(checkpoint.seen_fill_ids)
        self._seen_external_ids.update(checkpoint.seen_external_fill_ids)
        self._seen_fallback_keys.update(checkpoint.seen_fallback_keys)

    def accept(self, fill: Fill) -> Fill:
        """Return the fill fact once, rejecting duplicate fill identities."""

        if fill.external_fill_id is not None:
            if fill.external_fill_id in self._seen_external_ids:
                raise ValueError(
                    "Duplicate external_fill_id received by FillProcessor"
                )
            self._seen_external_ids.add(fill.external_fill_id)
            self._seen_fill_ids.add(fill.fill_id)
            emit_structured_event(
                logger_name=__name__,
                event_type="fill_fact",
                entity_type="fill",
                entity_id=fill.fill_id,
                lineage_id=fill.order_intent_id,
                stage="fill_processing",
                lifecycle_step="fill_accepted",
                decision="accept_fill",
                outcome="accepted",
                reason="external_fill_id",
                reason_code="external_fill_id",
                metadata={"external_fill_id": fill.external_fill_id},
            )
            return fill

        fallback_key = self._fallback_key(fill)
        if fallback_key in self._seen_fallback_keys:
            raise ValueError(
                "Duplicate fallback fill identity received by FillProcessor"
            )
        self._seen_fallback_keys.add(fallback_key)

        if fill.fill_id in self._seen_fill_ids:
            raise ValueError("Duplicate fill_id received by FillProcessor")
        self._seen_fill_ids.add(fill.fill_id)
        emit_structured_event(
            logger_name=__name__,
            event_type="fill_fact",
            entity_type="fill",
            entity_id=fill.fill_id,
            lineage_id=fill.order_intent_id,
            stage="fill_processing",
            lifecycle_step="fill_accepted",
            decision="accept_fill",
            outcome="accepted",
            reason=fallback_key[0],
            reason_code=fallback_key[0],
            metadata={"fallback_identity": "|".join(fallback_key)},
        )
        return fill

    def _fallback_key(self, fill: Fill) -> tuple[str, ...]:
        execution_report_id = fill.metadata.get("execution_report_id")
        execution_fragment = fill.metadata.get("execution_fragment")
        if execution_report_id is not None:
            key = ["execution_report_id", execution_report_id]
            if execution_fragment is not None:
                key.extend(["execution_fragment", execution_fragment])
            return tuple(key)

        execution_fact_id = fill.metadata.get("execution_fact_id")
        if execution_fact_id is not None:
            return ("execution_fact_id", execution_fact_id)

        return (
            "execution_fact_fingerprint",
            fill.order_intent_id,
            fill.instrument.instrument_id,
            fill.side.value,
            self._decimal_string(fill.quantity),
            self._decimal_string(fill.price),
            self._decimal_string(fill.fee),
            fill.executed_at.isoformat(),
            fill.metadata.get("external_order_id", ""),
        )

    def _decimal_string(self, value: Decimal) -> str:
        return format(value, "f")

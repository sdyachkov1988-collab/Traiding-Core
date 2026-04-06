"""Fill intake for the first internal truth spine."""

from __future__ import annotations

from dataclasses import dataclass, field

from trading_core.domain.fills import Fill
from trading_core.domain.state import FillDedupCheckpoint


@dataclass(slots=True)
class IdempotentFillProcessor:
    """Accept fill facts once and expose them to the downstream spine."""

    _seen_external_ids: set[str] = field(default_factory=set)
    _seen_fill_ids: set[str] = field(default_factory=set)
    _seen_fallback_keys: set[tuple[str, str, str, str, str, str]] = field(default_factory=set)

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

        return ("fill_id", fill.fill_id)

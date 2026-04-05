"""Fill intake for the first internal truth spine."""

from __future__ import annotations

from dataclasses import dataclass, field

from trading_core.domain.fills import Fill


@dataclass(slots=True)
class IdempotentFillProcessor:
    """Accept fill facts once and expose them to the downstream spine."""

    # Known limitation for Minimal Core v1: duplicate tracking is in-memory only.
    # Persisting the full identity set across restart belongs to a later
    # hardening phase. The current restart bridge restores only the latest
    # processed internal fill id from persisted state.
    _seen_external_ids: set[str] = field(default_factory=set)
    _seen_fill_ids: set[str] = field(default_factory=set)
    _seen_fallback_keys: set[tuple[str, str, str, str, str, str]] = field(default_factory=set)

    def restore_processed_fill_id(self, fill_id: str | None) -> None:
        """Seed the processor with the latest persisted internal fill identity."""

        if fill_id is None:
            return
        self._seen_fill_ids.add(fill_id)

    def accept(self, fill: Fill) -> Fill:
        """Return the fill fact once, rejecting duplicate fill identities."""

        if fill.external_fill_id is not None:
            if fill.external_fill_id in self._seen_external_ids:
                raise ValueError(
                    "Duplicate external_fill_id received by FillProcessor"
                )
            self._seen_external_ids.add(fill.external_fill_id)
            return fill

        fallback_key = (
            fill.order_intent_id,
            fill.instrument.instrument_id,
            fill.side.value,
            str(fill.quantity),
            str(fill.price),
            str(fill.fee),
        )
        if fallback_key in self._seen_fallback_keys:
            raise ValueError(
                "Duplicate fallback fill identity received by FillProcessor"
            )
        self._seen_fallback_keys.add(fallback_key)

        if fill.fill_id in self._seen_fill_ids:
            raise ValueError("Duplicate fill_id received by FillProcessor")
        self._seen_fill_ids.add(fill.fill_id)
        return fill

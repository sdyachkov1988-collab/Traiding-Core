"""Fill intake for the first internal truth spine."""

from __future__ import annotations

from dataclasses import dataclass, field

from trading_core.domain.fills import Fill


@dataclass(slots=True)
class IdempotentFillProcessor:
    """Accept fill facts once and expose them to the downstream spine."""

    # Known limitation for Minimal Core v1: duplicate tracking is in-memory only.
    # Persisting these identities across restart belongs to a later hardening phase.
    _seen_external_ids: set[str] = field(default_factory=set)
    _seen_fill_ids: set[str] = field(default_factory=set)

    def accept(self, fill: Fill) -> Fill:
        """Return the fill fact once, rejecting duplicate fill identities."""

        if fill.external_fill_id is not None:
            if fill.external_fill_id in self._seen_external_ids:
                raise ValueError(
                    "Duplicate external_fill_id received by FillProcessor"
                )
            self._seen_external_ids.add(fill.external_fill_id)
            return fill

        if fill.fill_id in self._seen_fill_ids:
            raise ValueError("Duplicate fill_id received by FillProcessor")
        self._seen_fill_ids.add(fill.fill_id)
        return fill

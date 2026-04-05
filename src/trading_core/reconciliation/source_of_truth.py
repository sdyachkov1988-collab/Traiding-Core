"""Source-of-truth policy for reconciliation and recovery semantics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceOfTruthPolicy:
    """Document source-of-truth rules for different state classes."""

    execution_facts_source: str = "external_venue"
    market_data_source: str = "canonical_instrument_scoped_data_layer"
    position_truth_source: str = "external_execution_state_via_reconciliation"

    def requires_reconciliation_for_position(self) -> bool:
        """Position truth always requires reconciliation with external state."""

        return True

    def blocks_trading_on_position_conflict(self) -> bool:
        """Position conflicts block trading until an explicit resolve path."""

        return True

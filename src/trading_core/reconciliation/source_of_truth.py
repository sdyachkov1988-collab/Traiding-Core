"""Source-of-truth policy for reconciliation and recovery semantics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceOfTruthPolicy:
    """Document source-of-truth rules for different state classes."""

    local_picture_class: str = "local_observed_state"
    external_picture_class: str = "external_observed_state"
    derived_state_class: str = "derived_internal_state"
    reconciled_truth_class: str = "reconciliation_outcome_layer"
    execution_facts_source: str = "external_venue"
    market_data_source: str = "canonical_instrument_scoped_data_layer"
    position_truth_source: str = "external_execution_state_via_reconciliation"

    def authoritative_source_for_execution_facts(self) -> str:
        """Return the authoritative source for external execution facts."""

        return self.execution_facts_source

    def authoritative_source_for_market_data(self) -> str:
        """Return the authoritative source for market-data-derived context."""

        return self.market_data_source

    def authoritative_source_for_position_truth(self) -> str:
        """Return the authoritative source for trading-significant position truth."""

        return self.position_truth_source

    def reconciliation_outcome_is_distinct_from_observed_pictures(self) -> bool:
        """Reconciled truth is its own outcome layer, not a cosmetic state update."""

        return True

    def requires_reconciliation_for_position(self) -> bool:
        """Position truth always requires reconciliation with external state."""

        return True

    def blocks_trading_on_position_conflict(self) -> bool:
        """Position conflicts block trading until an explicit resolve path."""

        return True

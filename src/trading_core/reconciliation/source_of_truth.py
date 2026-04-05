"""Source-of-truth policy for reconciliation and recovery semantics."""

from __future__ import annotations

from dataclasses import dataclass

from trading_core.domain.unknown import SystemMode


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
    insufficient_basis_mode: SystemMode = SystemMode.READ_ONLY
    non_active_conflict_mode: SystemMode = SystemMode.READ_ONLY
    active_position_conflict_mode: SystemMode = SystemMode.SAFE_MODE

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

    def mode_for_insufficient_basis(self) -> SystemMode:
        """Return the minimum safe system mode for unresolved reconciliation basis."""

        return self.insufficient_basis_mode

    def mode_for_position_conflict(
        self,
        *,
        conflicts_with_active_trading: bool,
    ) -> SystemMode:
        """Return the failure-path mode for a conflicting reconciliation outcome."""

        if conflicts_with_active_trading:
            return self.active_position_conflict_mode
        return self.non_active_conflict_mode

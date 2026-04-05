"""Contracts for G1 state ownership and persistence."""

from __future__ import annotations

from typing import Protocol

from trading_core.domain.portfolio_state import PortfolioState
from trading_core.domain.state import FillDedupCheckpoint, PersistedStateSnapshot


class StateStore(Protocol):
    """Persist and load local state snapshots without reconciliation semantics."""

    def save(self, portfolio_state: PortfolioState) -> PersistedStateSnapshot:
        """Persist the current local state snapshot."""

    def save_with_fill_marker(
        self,
        portfolio_state: PortfolioState,
        processed_fill_id: str,
        dedup_checkpoint: FillDedupCheckpoint | None = None,
    ) -> PersistedStateSnapshot:
        """Persist the current local state snapshot and processed fill marker."""

    def load_latest(self) -> PersistedStateSnapshot | None:
        """Load the latest locally persisted snapshot, if present."""

"""Persisted state models for G1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now
from trading_core.domain.portfolio_state import PortfolioState


@dataclass(frozen=True, slots=True)
class PersistedStateSnapshot:
    """Minimal locally persisted state view for Minimal Core v1."""

    snapshot_id: str
    portfolio_state: PortfolioState
    saved_at: datetime
    last_processed_fill_id: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.saved_at, "saved_at")

    @classmethod
    def create(
        cls,
        *,
        portfolio_state: PortfolioState,
        last_processed_fill_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "PersistedStateSnapshot":
        """Create a local persisted snapshot from already-recognized state."""

        return cls(
            snapshot_id=new_internal_id("snapshot"),
            portfolio_state=portfolio_state,
            saved_at=utc_now(),
            last_processed_fill_id=last_processed_fill_id,
            metadata=dict(metadata or {}),
        )

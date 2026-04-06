"""Persisted state models for G1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

from trading_core.domain.common import new_internal_id, require_utc_datetime, utc_now
from trading_core.domain.execution import ExecutionReportKind
from trading_core.domain.portfolio_state import PortfolioState


@dataclass(frozen=True, slots=True)
class FillDedupCheckpoint:
    """Persisted fill-dedup identities used to restore restart safety."""

    seen_fill_ids: tuple[str, ...] = ()
    seen_external_fill_ids: tuple[str, ...] = ()
    seen_fallback_keys: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class PersistedOrderRecord:
    """Locally persisted order-side picture for restart and reconciliation."""

    order_intent_id: str
    external_order_id: str | None
    last_report_kind: ExecutionReportKind
    observed_at: datetime
    reason: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.observed_at, "observed_at")


@dataclass(frozen=True, slots=True)
class PersistedStateSnapshot:
    """Locally persisted state view for restart survivability."""

    snapshot_id: str
    portfolio_state: PortfolioState
    order_picture: Mapping[str, PersistedOrderRecord]
    saved_at: datetime
    last_processed_fill_id: str | None = None
    fill_dedup_checkpoint: FillDedupCheckpoint | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_utc_datetime(self.saved_at, "saved_at")

    @classmethod
    def create(
        cls,
        *,
        portfolio_state: PortfolioState,
        order_picture: Mapping[str, PersistedOrderRecord] | None = None,
        last_processed_fill_id: str | None = None,
        fill_dedup_checkpoint: FillDedupCheckpoint | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> "PersistedStateSnapshot":
        """Create a local persisted snapshot from already-recognized state."""

        return cls(
            snapshot_id=new_internal_id("snapshot"),
            portfolio_state=portfolio_state,
            order_picture=dict(order_picture or {}),
            saved_at=utc_now(),
            last_processed_fill_id=last_processed_fill_id,
            fill_dedup_checkpoint=fill_dedup_checkpoint,
            metadata=dict(metadata or {}),
        )

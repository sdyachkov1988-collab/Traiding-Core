"""Local state store implementation for G1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from trading_core.domain.common import InstrumentRef
from trading_core.domain.portfolio_state import PortfolioState, Position
from trading_core.domain.execution import ExecutionReportKind
from trading_core.domain.state import (
    FillDedupCheckpoint,
    PersistedOrderRecord,
    PersistedStateSnapshot,
)


class JsonFileStateStore:
    """Persist the latest local portfolio snapshot to a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save(
        self,
        portfolio_state: PortfolioState,
        *,
        order_picture: dict[str, PersistedOrderRecord] | None = None,
    ) -> PersistedStateSnapshot:
        """Persist the portfolio snapshot as the locally owned state view."""

        self._validate_portfolio_state(portfolio_state)
        if not self._is_pristine_snapshot_candidate(portfolio_state, order_picture):
            raise ValueError("save_requires_pristine_state_or_use_save_with_fill_marker")

        snapshot = PersistedStateSnapshot.create(
            portfolio_state=portfolio_state,
            order_picture=order_picture,
            metadata={
                "storage_format": "json",
                "accounting_policy": "assembly_level_fee_in_cost_basis",
            },
        )
        self._write_snapshot(snapshot)
        return snapshot

    def save_with_fill_marker(
        self,
        portfolio_state: PortfolioState,
        processed_fill_id: str,
        dedup_checkpoint: FillDedupCheckpoint | None = None,
        order_picture: dict[str, PersistedOrderRecord] | None = None,
    ) -> PersistedStateSnapshot:
        """Persist the portfolio snapshot and processed fill marker atomically."""

        self._validate_portfolio_state(portfolio_state)
        snapshot = PersistedStateSnapshot.create(
            portfolio_state=portfolio_state,
            order_picture=order_picture,
            last_processed_fill_id=processed_fill_id,
            fill_dedup_checkpoint=dedup_checkpoint,
            metadata={
                "storage_format": "json",
                "accounting_policy": "assembly_level_fee_in_cost_basis",
            },
        )
        self._write_snapshot(snapshot)
        return snapshot

    def load_latest(self) -> PersistedStateSnapshot | None:
        """Load the latest locally persisted portfolio snapshot, if any."""

        if not self._path.exists():
            return None

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return self._deserialize_snapshot(payload)

    def _write_snapshot(self, snapshot: PersistedStateSnapshot) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._serialize_snapshot(snapshot)
        temp_path = self._path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_path.replace(self._path)

    def _is_pristine_snapshot_candidate(
        self,
        portfolio_state: PortfolioState,
        order_picture: dict[str, PersistedOrderRecord] | None,
    ) -> bool:
        return (
            portfolio_state.positions == {}
            and portfolio_state.realized_pnl == Decimal("0")
            and portfolio_state.reserved_cash_balance == Decimal("0")
            and portfolio_state.metadata.get("reconcile_required") != "true"
            and not order_picture
        )

    def _serialize_snapshot(self, snapshot: PersistedStateSnapshot) -> dict[str, object]:
        positions = {}
        for instrument_id, position in snapshot.portfolio_state.positions.items():
            positions[instrument_id] = {
                "position_id": position.position_id,
                "instrument": {
                    "instrument_id": position.instrument.instrument_id,
                    "symbol": position.instrument.symbol,
                    "venue": position.instrument.venue,
                    "market_type": position.instrument.market_type,
                },
                "quantity": str(position.quantity),
                "average_entry_price": str(position.average_entry_price),
                "realized_pnl": str(position.realized_pnl),
                "updated_at": position.updated_at.isoformat(),
                "metadata": dict(position.metadata),
            }

        return {
            "snapshot_id": snapshot.snapshot_id,
            "saved_at": snapshot.saved_at.isoformat(),
            "last_processed_fill_id": snapshot.last_processed_fill_id,
            "order_picture": {
                order_intent_id: {
                    "order_intent_id": order_record.order_intent_id,
                    "external_order_id": order_record.external_order_id,
                    "last_report_kind": order_record.last_report_kind.value,
                    "observed_at": order_record.observed_at.isoformat(),
                    "reason": order_record.reason,
                    "metadata": dict(order_record.metadata),
                }
                for order_intent_id, order_record in snapshot.order_picture.items()
            },
            "fill_dedup_checkpoint": (
                None
                if snapshot.fill_dedup_checkpoint is None
                else {
                    "seen_fill_ids": list(snapshot.fill_dedup_checkpoint.seen_fill_ids),
                    "seen_external_fill_ids": list(
                        snapshot.fill_dedup_checkpoint.seen_external_fill_ids
                    ),
                    "seen_fallback_keys": [
                        list(key)
                        for key in snapshot.fill_dedup_checkpoint.seen_fallback_keys
                    ],
                }
            ),
            "metadata": dict(snapshot.metadata),
            "portfolio_state": {
                "portfolio_state_id": snapshot.portfolio_state.portfolio_state_id,
                "cash_balance": str(snapshot.portfolio_state.cash_balance),
                "available_cash_balance": str(snapshot.portfolio_state.available_cash_balance),
                "reserved_cash_balance": str(snapshot.portfolio_state.reserved_cash_balance),
                "realized_pnl": str(snapshot.portfolio_state.realized_pnl),
                "equity": str(snapshot.portfolio_state.equity),
                "balances": {
                    balance_name: str(balance_value)
                    for balance_name, balance_value in snapshot.portfolio_state.balances.items()
                },
                "updated_at": snapshot.portfolio_state.updated_at.isoformat(),
                "metadata": dict(snapshot.portfolio_state.metadata),
                "positions": positions,
            },
        }

    def _deserialize_snapshot(self, payload: dict[str, object]) -> PersistedStateSnapshot:
        raw_portfolio = payload["portfolio_state"]
        if not isinstance(raw_portfolio, dict):
            raise TypeError(f"expected dict, got {type(raw_portfolio).__name__}")
        raw_positions = raw_portfolio["positions"]
        if not isinstance(raw_positions, dict):
            raise TypeError(f"expected dict, got {type(raw_positions).__name__}")

        positions: dict[str, Position] = {}
        for instrument_id, raw_position in raw_positions.items():
            if not isinstance(raw_position, dict):
                raise TypeError(f"expected dict, got {type(raw_position).__name__}")
            raw_instrument = raw_position["instrument"]
            if not isinstance(raw_instrument, dict):
                raise TypeError(f"expected dict, got {type(raw_instrument).__name__}")
            positions[str(instrument_id)] = Position(
                position_id=str(raw_position["position_id"]),
                instrument=InstrumentRef(
                    instrument_id=str(raw_instrument["instrument_id"]),
                    symbol=str(raw_instrument["symbol"]),
                    venue=str(raw_instrument["venue"]),
                    market_type=str(raw_instrument["market_type"]),
                ),
                quantity=Decimal(str(raw_position["quantity"])),
                average_entry_price=Decimal(str(raw_position["average_entry_price"])),
                realized_pnl=Decimal(str(raw_position["realized_pnl"])),
                updated_at=self._parse_utc_datetime(str(raw_position["updated_at"]), "position.updated_at"),
                metadata=dict(raw_position["metadata"]),
            )

        portfolio_state = PortfolioState(
            portfolio_state_id=str(raw_portfolio["portfolio_state_id"]),
            cash_balance=Decimal(str(raw_portfolio["cash_balance"])),
            available_cash_balance=Decimal(
                str(raw_portfolio.get("available_cash_balance", raw_portfolio["cash_balance"]))
            ),
            reserved_cash_balance=Decimal(
                str(raw_portfolio.get("reserved_cash_balance", "0"))
            ),
            realized_pnl=Decimal(str(raw_portfolio["realized_pnl"])),
            equity=Decimal(
                str(
                    raw_portfolio.get(
                        "equity",
                        raw_portfolio["cash_balance"],
                    )
                )
            ),
            balances={
                str(balance_name): Decimal(str(balance_value))
                for balance_name, balance_value in dict(
                    raw_portfolio.get("balances", {"cash": raw_portfolio["cash_balance"]})
                ).items()
            },
            positions=positions,
            updated_at=self._parse_utc_datetime(str(raw_portfolio["updated_at"]), "portfolio_state.updated_at"),
            metadata=dict(raw_portfolio["metadata"]),
        )
        self._validate_portfolio_state(portfolio_state)
        raw_checkpoint = payload.get("fill_dedup_checkpoint")
        return PersistedStateSnapshot(
            snapshot_id=str(payload["snapshot_id"]),
            portfolio_state=portfolio_state,
            order_picture=self._deserialize_order_picture(payload.get("order_picture", {})),
            saved_at=self._parse_utc_datetime(str(payload["saved_at"]), "saved_at"),
            last_processed_fill_id=(
                None
                if payload.get("last_processed_fill_id") is None
                else str(payload["last_processed_fill_id"])
            ),
            fill_dedup_checkpoint=self._deserialize_fill_dedup_checkpoint(raw_checkpoint),
            metadata=dict(payload["metadata"]),
        )

    def _deserialize_fill_dedup_checkpoint(
        self,
        raw_checkpoint: object,
    ) -> FillDedupCheckpoint | None:
        if raw_checkpoint is None:
            return None
        if not isinstance(raw_checkpoint, dict):
            raise TypeError(
                f"expected dict, got {type(raw_checkpoint).__name__}"
            )

        raw_fill_ids = raw_checkpoint.get("seen_fill_ids", [])
        raw_external_ids = raw_checkpoint.get("seen_external_fill_ids", [])
        raw_fallback_keys = raw_checkpoint.get("seen_fallback_keys", [])
        if not isinstance(raw_fill_ids, list):
            raise TypeError(f"expected list, got {type(raw_fill_ids).__name__}")
        if not isinstance(raw_external_ids, list):
            raise TypeError(f"expected list, got {type(raw_external_ids).__name__}")
        if not isinstance(raw_fallback_keys, list):
            raise TypeError(f"expected list, got {type(raw_fallback_keys).__name__}")

        fallback_keys: list[tuple[str, str, str, str, str, str]] = []
        for raw_key in raw_fallback_keys:
            if not isinstance(raw_key, (list, tuple)):
                raise TypeError("fill_dedup_checkpoint.seen_fallback_keys entries must be sequences")
            fallback_keys.append(tuple(str(part) for part in raw_key))

        return FillDedupCheckpoint(
            seen_fill_ids=tuple(str(fill_id) for fill_id in raw_fill_ids),
            seen_external_fill_ids=tuple(str(external_id) for external_id in raw_external_ids),
            seen_fallback_keys=tuple(fallback_keys),
        )

    def _deserialize_order_picture(
        self,
        raw_order_picture: object,
    ) -> dict[str, PersistedOrderRecord]:
        if not isinstance(raw_order_picture, dict):
            raise TypeError(
                f"expected dict, got {type(raw_order_picture).__name__}"
            )

        order_picture: dict[str, PersistedOrderRecord] = {}
        for order_intent_id, raw_record in raw_order_picture.items():
            if not isinstance(raw_record, dict):
                raise TypeError(f"expected dict, got {type(raw_record).__name__}")
            order_picture[str(order_intent_id)] = PersistedOrderRecord(
                order_intent_id=str(raw_record["order_intent_id"]),
                external_order_id=(
                    None
                    if raw_record.get("external_order_id") is None
                    else str(raw_record["external_order_id"])
                ),
                last_report_kind=ExecutionReportKind(str(raw_record["last_report_kind"])),
                observed_at=self._parse_utc_datetime(
                    str(raw_record["observed_at"]),
                    "order_picture.observed_at",
                ),
                reason=None if raw_record.get("reason") is None else str(raw_record["reason"]),
                metadata=dict(raw_record.get("metadata", {})),
            )
        return order_picture

    def _parse_utc_datetime(self, raw_value: str, field_name: str) -> datetime:
        parsed = datetime.fromisoformat(raw_value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise TypeError(f"{field_name} must be timezone-aware UTC")
        if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise TypeError(f"{field_name} must be UTC")
        return parsed

    def _validate_portfolio_state(self, portfolio_state: PortfolioState) -> None:
        if portfolio_state.cash_balance < Decimal("0") and portfolio_state.metadata.get("reconcile_required") != "true":
            raise ValueError("negative_cash_balance_requires_reconcile_flag")

"""Minimal structured logging helpers for Wave 3 hardening."""

from __future__ import annotations

import json
import logging
from typing import Mapping

from trading_core.domain.common import utc_now


def emit_structured_event(
    *,
    logger_name: str,
    event_type: str,
    entity_type: str,
    entity_id: str | None = None,
    lineage_id: str | None = None,
    stage: str | None = None,
    lifecycle_step: str | None = None,
    decision: str,
    outcome: str,
    reason: str | None = None,
    reason_code: str | None = None,
    metadata: Mapping[str, str] | None = None,
) -> None:
    """Emit one normalized structured log event for hardening coverage."""

    payload: dict[str, object] = {
        "timestamp": utc_now().isoformat(),
        "event_type": event_type,
        "entity_type": entity_type,
        "decision": decision,
        "outcome": outcome,
        "reason": "" if reason is None else reason,
        "reason_code": reason_code or reason or "",
    }
    if stage is None and lifecycle_step is None:
        raise ValueError("structured logs require stage or lifecycle_step")
    if stage is not None:
        payload["stage"] = stage
    if lifecycle_step is not None:
        payload["lifecycle_step"] = lifecycle_step
    if entity_id is not None:
        payload["entity_id"] = entity_id
    if lineage_id is not None:
        payload["lineage_id"] = lineage_id
    if metadata:
        payload["metadata"] = dict(metadata)

    logging.getLogger(logger_name).info(
        json.dumps(payload, sort_keys=True, default=str)
    )

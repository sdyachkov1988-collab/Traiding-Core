"""Common domain primitives shared across Minimal Core v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Mapping
from uuid import uuid4


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


def new_internal_id(prefix: str) -> str:
    """Create a simple internal identifier for domain objects."""

    return f"{prefix}_{uuid4().hex}"


@dataclass(frozen=True, slots=True)
class InstrumentRef:
    """Minimal instrument identity used across early seams."""

    instrument_id: str
    symbol: str
    venue: str
    market_type: str = "spot"


@dataclass(frozen=True, slots=True)
class PriceLevel:
    """Price/quantity pair expressed with Decimal semantics."""

    price: Decimal
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class MetadataCarrier:
    """Shared metadata container for lineage and observability hints."""

    metadata: Mapping[str, str] = field(default_factory=dict)

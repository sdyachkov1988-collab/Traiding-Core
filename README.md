# Trading Core

`Trading Core` is a Python 3.11+ implementation of a `Minimal Core v1` trading engine, plus the first next-stage seams from Tracks B and C. The repository now contains a stable Wave 1 vertical slice, remediation fixes from Tracks A and B, and explicit Wave 2-style modules that are present in code without being silently promoted into the canonical Wave 1 active contour.

## Current Repository State

Closed Wave 1 / `Minimal Core v1` vertical slice:

- `Package A` - normalized input and early context seam
- `Package B` - strategy decision boundary
- `Package C` - risk verdict boundary
- `Package D1/D2` - order builder and pre-execution guard
- `Package E` - execution boundary
- `Package F` - fill-driven state spine
- `Package G1/G2` - local state store and startup reconciliation

Implemented next-stage seams now present in the repository:

- `Wave 2A` - canonical timeframe store and `TimeframeContext` foundation
- `Wave 2B` - `ContextGate`
- `Wave 2C` - unknown-state and system-mode semantics
- `Wave 2D` - reconciliation operating loop and recovery coordinator
- `Wave 2E` - position-originated close routing contour

## Active Wave 1 Path

The active `Wave 1G` acceptance contour is `MTF-first`, but phase-correct:

`market input -> Wave1MtfContext -> MTF strategy -> risk -> builder -> guard -> execution -> fill -> position -> portfolio -> state -> startup reconciliation`

Important boundary:

- Wave 1 uses a minimal `Wave1MtfContext` input seam for the active path
- full `TimeframeContext + ContextGate` exists in the repository as next-stage capability
- those seams are not silently redefined here as the mandatory canonical Wave 1 contour

Legacy `BarDirectionStrategy` remains in the project as reference-only behavior, not as the active acceptance strategy.

## Track A / Track B Remediation Status

The repository now includes the remediation outcomes that make the core materially safer:

- risk sizing uses `reference_price` and step-aligned base quantity
- spot `SELL` requires real position basis
- impossible oversell is explicit conflict, not silent clipping
- zero-quantity zombie positions are removed from portfolio truth
- builder rechecks quantity after rounding
- acceptance path uses an execution-to-fill seam instead of manual fill assembly
- fill idempotency covers fallback identity and restart restore bridge
- context/data integrity now includes history-depth warmup, temporal alignment, monotonic bar updates, source event time, and early readiness checks
- UTC-aware datetime validation is enforced across canonical domain objects

## Tolerance Semantics

`SimpleStartupReconciler` keeps:

- `cash_tolerance = Decimal("0")`
- `quantity_tolerance = Decimal("0")`

This means exact `Decimal` equality by default. Any tolerant comparison must be chosen explicitly by the caller; there is no implicit fuzzy matching.

## Running Tests

```bash
pytest
```

## Architectural Invariants

- `Decimal` is used for prices, quantities, and monetary values
- canonical domain datetimes are UTC-aware
- domain objects are immutable dataclasses
- local snapshots are written atomically
- fill processing is idempotent within the current process and restart bridge
- impossible fill/state conflicts are surfaced explicitly, not normalized away

## Docs Map

- [`docs/spec/index.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\spec\index.md) - source spec extraction
- [`docs/implementation_status.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\implementation_status.md) - current status after Tracks A, B, and C remediation work
- [`docs/project_layout.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\project_layout.md) - package and seam layout

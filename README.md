# Trading Core

`Trading Core` is a Python 3.11+ implementation of a `Minimal Core v1` trading engine with a closed Wave 1 working contour and several implemented next-stage seams. The repository contains the remediated Wave 1 vertical slice, plus experimental prototypes for context, recovery, reconciliation loop, and close routing.

## Current Repository State

Closed Wave 1 / `Minimal Core v1` vertical slice:

- `Package A` - normalized input and early context seam
- `Package B` - strategy decision boundary
- `Package C` - risk verdict boundary
- `Package D1/D2` - order builder and pre-execution guard
- `Package E` - execution boundary
- `Package F` - fill-driven state spine
- `Package G1/G2` - local state store and startup reconciliation

Wave 1 active contour uses `Wave1MtfContextAssembler` and `MtfBarAlignmentStrategy`. Additional seams such as `ContextGate`, `RecoveryCoordinator`, and `CloseIntentRouter` are implemented as experimental next-stage prototypes. See [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md).

## Active Wave 1 Path

The current working path is:

`TimeframeSyncEvent -> Wave1MtfContext -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

Important boundary:

- Wave 1 active acceptance is `MTF-first`
- the strategy receives `entry timeframe + mandatory HTF input` through the core
- full `TimeframeContext` and `ContextGate` exist in the repository, but are not the mandatory canonical Wave 1 contour

Legacy `BarDirectionStrategy` remains in the project as reference-only behavior.

## Track A / Track B / Track C Status

The repository now includes the remediation outcomes that make the core materially safer:

- risk sizing uses `reference_price` and step-aligned base quantity
- spot `SELL` requires real position basis
- impossible oversell is explicit conflict, not silent clipping
- zero-quantity zombie positions are removed from portfolio truth
- builder rechecks quantity after rounding
- acceptance path uses an execution-to-fill seam instead of manual fill assembly
- fill idempotency covers external identity, fallback replay, restart restore bridge, and mixed-source replay protection
- context/data integrity includes history-depth warmup, temporal alignment, monotonic bar updates, source event time, and early readiness checks
- canonical domain datetimes are enforced as UTC-aware

## Tolerance Semantics

`SimpleStartupReconciler` keeps:

- `cash_tolerance = Decimal("0")`
- `quantity_tolerance = Decimal("0")`

This means exact `Decimal` equality by default. Any tolerant comparison must be chosen explicitly by the caller; there is no implicit fuzzy matching.

## Running Tests

The current suite is green: `134 passed`.

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

- [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md) - active / experimental / reserved repository map
- [`docs/spec/index.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\spec\index.md) - source spec extraction
- [`docs/implementation_status.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\implementation_status.md) - implementation status after remediation work
- [`docs/project_layout.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\project_layout.md) - package and seam layout

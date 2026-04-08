# Trading Core

`Trading Core` is a Python 3.11+ implementation of a `Minimal Core v1` trading engine with a closed Wave 1 working contour and implemented Wave 2 seams. The repository now includes the Wave 1 and Wave 2 critical fixes from the acceptance remediation TZ, while keeping the broader architecture and phase boundaries intact.

## Current Repository State

Closed Wave 1 / `Minimal Core v1` vertical slice:

- `Package A` - normalized input and early context seam
- `Package B` - strategy decision boundary
- `Package C` - risk verdict boundary
- `Package D1/D2` - order builder and pre-execution guard
- `Package E` - execution boundary
- `Package F` - fill-driven state spine
- `Package G1/G2` - local state store and startup reconciliation

Implemented next-stage seams with critical-fix coverage:

- `2A` canonical timeframe store and `TimeframeContext`
- `2B` `ContextGate` and formal admission rules for readiness, warmup, stale/gap/lookahead, session, and maintenance
- `2C` unknown-state classifier and monotonic safety modes
- `2D` reconciliation loop coordinator across startup, periodic, on-error, and operator-command triggers
- `2E` position-originated close routing

The current runtime/tests use formal `TimeframeContext + ContextGate` ahead of `MtfBarAlignmentStrategy`. Earlier `Wave1MtfContext` naming is still present in the repo as legacy phase wording, but it is not the primary acceptance/runtime path anymore. See [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md).

## Active Runtime Path

The current working path is:

`TimeframeSyncEvent -> TimeframeContext -> ContextGate -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

Important boundary:

- Wave 1 active acceptance remains `MTF-first`
- the strategy receives `entry timeframe + mandatory HTF input` through the formal context seam used in runtime/tests
- `Wave1MtfContext` remains in the codebase as early/legacy naming, not as the primary runtime contour label

Legacy `BarDirectionStrategy` remains in the project as reference-only behavior.

## Critical Fix Baseline

The current codebase includes the critical fixes required by the remediation TZ:

- builder and close-builder use real step-multiple alignment rather than `quantize` shortcuts
- startup reconciliation no longer hides shared-instrument mismatches behind zero-quantity pruning
- startup reconciliation now compares order picture plus material portfolio-level fields
- state store now supports order-side snapshot persistence without requiring a processed-fill marker path
- position, portfolio, risk, and state seams enforce instrument coherence and reject contradictory state
- `TimeframeContext` and `ContextGate` formally reject malformed context/config instead of admitting or crashing
- `ContextGate` now expresses session and maintenance restrictions through formal gate reasons instead of ad hoc status
- recovery mode transitions are monotonic and do not auto-downgrade from `SAFE_MODE` or `FROZEN`
- reconciliation loop now exposes a unified four-trigger capability including operator-command requests
- `data_gap_detected` has an explicit recovery path once contiguous bars resume

## Tolerance Semantics

`SimpleStartupReconciler` keeps:

- `cash_tolerance = Decimal("0")`
- `quantity_tolerance = Decimal("0")`

This means exact `Decimal` equality by default. Any tolerant comparison must be chosen explicitly by the caller; there is no implicit fuzzy matching.

## Running Tests

The current suite is green: `244 passed`.

```bash
pytest
```

## Architectural Invariants

- `Decimal` is used for prices, quantities, and monetary values
- canonical domain datetimes are UTC-aware
- domain objects are immutable dataclasses
- local snapshots are written atomically
- fill processing is idempotent within the current process and restart bridge
- impossible fill/state/context conflicts are surfaced explicitly, not normalized away

## Docs Map

- [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md) - active / implemented / reserved repository map
- [`docs/spec/index.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\spec\index.md) - extracted source specification set
- [`docs/implementation_status.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\implementation_status.md) - implementation snapshot after critical fixes
- [`docs/project_layout.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\project_layout.md) - package and seam layout

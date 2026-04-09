# Trading Core

`Trading Core` is a Python 3.11+ implementation of a `Minimal Core v1` trading engine with a closed Wave 1 working contour and selected implemented next-stage seams. The repository includes the Wave 1 and Wave 2 critical fixes from the acceptance remediation TZ while keeping the broader architecture and phase boundaries intact.

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

The repository keeps one active Wave 1 acceptance slice plus a set of implemented next-stage seams:

- `Wave 1G` acceptance uses the phase-scoped `Wave1MtfContext` seam and is exercised by [`tests/test_acceptance_wave1g_minimal_core.py`](C:\Users\Sergey\Desktop\Traiding Engine\tests\test_acceptance_wave1g_minimal_core.py)
- next-stage modules such as `TimeframeContextAssembler`, `ContextGate`, `RecoveryCoordinator`, `UnknownStateClassifier`, and `CloseIntentRouter` are implemented and test-covered as separate seams

## Pre-Wave3 Reading Rule

- Wave 3 hardening is not started in this repository state;
- governance remains an external policy-layer and is not implemented as an active core layer;
- the repo still contains pre-Wave3 known gaps where documents do not yet justify a code-side harmonization pass.

## Acceptance And Implemented Seam Paths

`Wave 1G` / `Minimal Core v1` acceptance path:

`MarketEvent -> Wave1MtfContext -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

Important boundary:

- `Wave 1G` acceptance stays on Wave 1 seams and the minimal MTF input seam
- `TimeframeContext + ContextGate` remain in the repo as implemented next-stage seam modules, not as one active governance-owned runtime contour
- `Wave1MtfContext` is explicit phase naming for the Wave 1 acceptance slice

Known pre-Wave3 gaps:

- the exported strategy surface still spans both the phase-scoped `Wave1MtfContext` and the later `TimeframeContext` family; this is left in place until documents allow a non-invented harmonization pass;
- `Wave1MtfContextAssembler` currently reuses later timeframe foundation internals; the repo keeps this as an explicit pre-Wave3 limitation rather than claiming a fully separated phase surface;
- close routing exists as a Wave 2E seam, but its precise contract reading relative to the broader decision-chain invariants is still treated as a known unresolved contract gap before harmonization/governance.

## Critical Fix Baseline

The current codebase includes the critical fixes required by the remediation TZ:

- builder and close-builder use real step-multiple alignment rather than `quantize` shortcuts
- startup reconciliation no longer hides shared-instrument mismatches behind zero-quantity pruning
- startup reconciliation now compares order picture plus material portfolio-level fields
- state store now supports order-side snapshot persistence without requiring a processed-fill marker path
- execution-to-fill handoff is now core-owned in `ExecutionHandoff`; active runtime and acceptance paths no longer call adapter-specific fill materializers
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

The current suite is green: `239 passed`.

```bash
pytest
```

## Architectural Invariants

- `Decimal` is used for prices, quantities, and monetary values
- canonical domain datetimes are UTC-aware
- domain objects are immutable dataclasses
- local snapshots are written atomically
- fill processing keeps explicit identity tracking and persisted checkpoint support
- execution adapters remain the only external boundary; fill handoff normalization lives in Package E
- impossible fill/state/context conflicts are surfaced explicitly, not normalized away

## Docs Map

- [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md) - active / implemented / reserved repository map
- [`docs/spec/index.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\spec\index.md) - extracted source specification set
- [`docs/implementation_status.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\implementation_status.md) - implementation snapshot after critical fixes
- [`docs/project_layout.md`](C:\Users\Sergey\Desktop\Traiding Engine\docs\project_layout.md) - package and seam layout

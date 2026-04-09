# Implementation Status

## Current status

The repository now contains three categories of code:

- a dedicated `Wave 1G` acceptance contour for `Minimal Core v1`
- an implemented next-stage seam set that is phase-separate from the Wave 1 acceptance contour
- reserved areas that remain outside current scope

Pre-Wave3 interpretation:

- this repository state is functional before Wave 3 hardening, not after it;
- Wave 2 seams are present, but the repo does not claim full contract harmonization across all layers;
- governance remains external to the active core layer set.

## Wave 1G acceptance contour

The dedicated `Wave 1G` acceptance path is:

`MarketEvent -> Wave1MtfContext -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

Meaning:

- `Wave 1G` now validates `Minimal Core v1` on Wave 1 seams plus the minimal MTF input seam
- this slice does not depend on `TimeframeContext`, `ContextGate`, or `RecoveryCoordinator`
- the acceptance path is exercised by `tests/test_acceptance_wave1g_minimal_core.py`
- execution-to-fill normalization inside this slice is owned by `ExecutionHandoff`, not by adapter-specific helpers

## Implemented next-stage seams

Meaning:

- the next-stage seam family no longer depends on a separate legacy single-bar strategy contour
- the strategy-related seam receives `entry timeframe + mandatory HTF input` through the formal context seam
- `ContextGate` exists as a separate next-stage gate seam
- fill identity is handled separately from order identity inside the fill processor and execution-to-fill handoff

Naming split:

- `Wave1MtfContext` remains as earlier phase-scoped / legacy naming for the Wave 1 acceptance slice
- `TimeframeContext + ContextGate` remain implemented as next-stage seams
- Wave 1 scope remains `Minimal Core v1`; this does not add governance or Wave 3 runtime ownership

## Wave 1 boundary ownership

- `Package A` - normalized input and early context seam
- `Package B` - strategy decision boundary
- `Package C` - risk verdict boundary
- `Package D` - order builder and pre-execution guard
- `Package E` - execution boundary
- `Package F` - fill-driven state spine
- `Package G` - local state store and startup reconciliation

## Implemented Wave 2 seams

The following seams are implemented in the repository and covered by tests, but are not part of the Wave 1 active contour:

- `src/trading_core/context/`
  canonical timeframe store, `TimeframeContextAssembler`, `ContextGate`, `BarAlignmentPolicy`, `ClosedBarPolicy`, `FreshnessPolicy`
- `src/trading_core/reconciliation/coordinator.py`
  `RecoveryCoordinator` and non-startup reconciliation loop request handling
- `src/trading_core/recovery/classifier.py`
  unknown-state classifier and system-mode transitions
- `src/trading_core/positions/close_router.py`
  position-originated close routing contour
- `src/trading_core/domain/reconciliation_extended.py`
  extended reconciliation request / outcome / verdict family

These seams are present in code and test-covered. They should be interpreted as implemented next-stage seams rather than as mandatory Wave 1 behavior.

## Known pre-Wave3 gaps

- the exported strategy surface still spans both the Wave 1 phase-scoped MTF context and the later `TimeframeContext` family;
- the Wave 1 assembler currently reuses later timeframe-foundation internals;
- close routing is present as a Wave 2E seam, but its exact contract reading against broader decision-chain invariants is left as an unresolved pre-harmonization gap.

## Reserved seams outside current scope

The following remain outside current scope:

- governance layer
- multi-instrument portfolio orchestration
- multi-exchange orchestration
- derivatives / leveraged products
- full periodic / on-error reconciliation policy and governance decisions
- production execution adapter family

## Critical-fix outcomes

The repository reflects the completed remediation work from the Wave 1 / Wave 2 critical-fixes TZ:

- risk sizing uses `reference_price` and step-aligned base sizing
- spot `SELL` requires a real current position basis
- impossible oversell is explicit conflict instead of silent clipping
- zero-quantity zombie positions are removed from portfolio truth
- builder and close-builder use real step-multiple alignment instead of `quantize` shortcuts
- Package E owns the execution-to-fill handoff through `ExecutionHandoff`
- fill identity handling remains explicit inside the fill processor and persisted checkpoint path
- context/data integrity includes history-depth warmup, temporal alignment, monotonic timeframe updates, `source_event_time -> event_time`, early readiness guarding, malformed-context rejection, and gap recovery after contiguous updates resume
- context gate includes formal session restriction and maintenance restriction branches with domain-level reasons
- startup reconciliation no longer hides shared-instrument mismatch after zero-quantity pruning
- startup reconciliation compares orders + positions + portfolio-level picture
- state store exposes an order-side persistence path without forcing a processed-fill marker
- risk, position, portfolio, and close-routing seams reject cross-instrument contradiction explicitly
- recovery mode transitions do not auto-downgrade from `SAFE_MODE` or `FROZEN`
- reconciliation loop exposes startup, periodic, on-error, and operator-command triggers as one formal capability
- canonical datetime fields are required to be UTC-aware

## Tolerance semantics

`SimpleStartupReconciler` defaults remain strict:

- `cash_tolerance = Decimal("0")`
- `quantity_tolerance = Decimal("0")`

Interpretation:

- `0` means exact `Decimal` equality
- tolerance is not silently widened by default
- any relaxed comparison must be chosen explicitly by the caller

## Practical reading rule

- `tests/test_acceptance_wave1g_minimal_core.py` is the truthful `Wave 1G` acceptance slice
- next-stage seam tests live in the package-level `2A-2E` test files rather than in one active runtime contour file
- `Wave1MtfContext` naming is retained as legacy phase wording for the Wave 1 acceptance seam
- source `docs/spec/` remain the roadmap authority; this file is the repo truth snapshot

## Wave 1G acceptance checklist

- one MTF-aware market input path reaches `Position` and `PortfolioState` through `Wave1MtfContext`
- restart restores persisted state
- startup reconciliation runs on restored state
- execution boundary does not leak into strategy, risk, or state ownership
- active acceptance path does not depend on `TimeframeContext + ContextGate`
- fill identity remains separate from order identity

## Current test status

- full suite: `239 passed`
- the suite includes targeted regressions for the Wave 1 / Wave 2 critical-fix cases

- [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md) is the quickest status map
- this file is the working implementation snapshot
- `docs/spec/` remains the reference set for roadmap meaning

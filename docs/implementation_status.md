# Implementation Status

## Current status

The repository now contains three categories of code:

- an active Wave 1 working contour
- implemented Wave 2 seams that are phase-separate from the Wave 1 active contour
- reserved areas that remain outside current scope

## Active Wave 1 contour

The active acceptance path is `MTF-first` and phase-correct for Wave 1:

`TimeframeSyncEvent -> Wave1MtfContext -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

Meaning:

- the active path no longer uses the legacy single-bar strategy
- the strategy receives `entry timeframe + mandatory HTF input` through the core
- fill identity is handled separately from order identity inside the fill processor and execution-to-fill handoff
- the active Wave 1 contour does not require full `TimeframeContext + ContextGate` canonization

## Closed Wave 1 scope

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
- acceptance uses a real execution-to-fill handoff helper
- fill idempotency covers fallback replay, restart restore bridge, and mixed-source replay
- context/data integrity includes history-depth warmup, temporal alignment, monotonic timeframe updates, `source_event_time -> event_time`, early readiness guarding, malformed-context rejection, and gap recovery after contiguous updates resume
- context gate includes formal session restriction and maintenance restriction branches with domain-level reasons
- startup reconciliation no longer hides shared-instrument mismatch after zero-quantity pruning
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

## Wave 1G acceptance checklist

- one MTF-aware market input path reaches `Position` and `PortfolioState`
- restart restores persisted state
- startup reconciliation runs on restored state
- execution boundary does not leak into strategy, risk, or state ownership
- active acceptance path does not depend on the legacy single-bar strategy
- fill identity remains separate from order identity

## Current test status

- full suite: `240 passed`
- the suite includes targeted regressions for the Wave 1 / Wave 2 critical-fix cases

## Practical reading rule

- [`CURRENT_STATUS.md`](C:\Users\Sergey\Desktop\Traiding Engine\CURRENT_STATUS.md) is the quickest status map
- this file is the working implementation snapshot
- `docs/spec/` remains the reference set for roadmap meaning

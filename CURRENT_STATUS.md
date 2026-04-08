# Current Status

## Active - runtime contour

The following modules are part of the real working runtime/acceptance contour in the repository:

- `src/trading_core/context/`
  `TimeframeContextAssembler`, `ContextGate`, `BarAlignmentPolicy`, `ClosedBarPolicy`, `FreshnessPolicy`
- `src/trading_core/strategy/`
  `MtfBarAlignmentStrategy`
- `src/trading_core/risk/`
  `ConfidenceCapRiskEvaluator`
- `src/trading_core/execution/`
  builder, guard, adapter, fill handoff, and fill processor
- `src/trading_core/positions/engine.py`
- `src/trading_core/portfolio/engine.py`
- `src/trading_core/state/`
- `src/trading_core/reconciliation/startup.py`

Active runtime path:

`TimeframeSyncEvent -> TimeframeContext -> ContextGate -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

Naming note:

- `Wave1MtfContext` / `Wave1MtfContextAssembler` remain in the repository as earlier phase-scoped naming
- active runtime/tests use formal `TimeframeContext + ContextGate`
- this does not promote governance-layer or Wave 3 behavior into the contour; it only reflects the actual runtime seam used by the repo

## Implemented - Wave 2 seams present in the repository

The following seams exist in code, are covered by tests, and include the current critical-fix baseline. They are still not the canonical Wave 1 acceptance contour:

- `src/trading_core/context/`
  `TimeframeContextAssembler`, `ContextGate`, `BarAlignmentPolicy`, `ClosedBarPolicy`, `FreshnessPolicy`
- `src/trading_core/reconciliation/coordinator.py`
- `src/trading_core/recovery/classifier.py`
- `src/trading_core/positions/close_router.py`
- `src/trading_core/domain/reconciliation_extended.py`

Operational meaning:

- `2A` enforces timeframe, instrument, and flag/depth coherence in `TimeframeContext`
- `2B` returns formal gate verdicts for malformed, stale, missing, gap-bearing, session-restricted, and maintenance-restricted context
- `2C` keeps `SystemMode` transitions monotonic by safety severity
- `2D` supports startup, periodic, on-error, and operator-command reconciliation requests and translates unresolved outcomes into explicit recovery posture changes
- `2E` validates close-route instrument coherence before handoff to guard/execution

These modules are implemented and usable, but they should still be read as next-stage seams rather than as the full Wave 1 scope definition from the source documents.

## Current acceptance baseline

The repository includes the Wave 1 and Wave 2 critical fixes from the remediation TZ:

- true step-multiple alignment in execution builders
- strict instrument coherence across risk, position, portfolio, and close routing
- stricter persisted-state and portfolio invariants
- startup reconciliation that does not hide shared-state mismatch after pruning
- startup reconciliation compares order picture plus portfolio-level fields instead of only cash and position quantity
- state store exposes an order-side persistence path without requiring a processed fill marker
- formal malformed-context handling in `ContextGate`
- formal session and maintenance restrictions in `ContextGate`
- data-gap recovery when normal bar continuity resumes
- monotonic `SAFE_MODE` / `FROZEN` posture handling
- unified four-trigger Wave 2D reconciliation request capability

Current test status: `244 passed`

## Reserved - outside current scope

The following areas remain outside the repository's current implementation scope:

- governance layer
- multi-instrument orchestration
- multi-exchange orchestration
- derivatives / leveraged products
- full periodic / on-error reconciliation policy and governance decisions
- production execution adapter family

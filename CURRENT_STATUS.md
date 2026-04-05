# Current Status

## Active - Wave 1 working contour

The following modules are part of the real working Wave 1 vertical slice:

- `src/trading_core/input/`
  `Wave1MtfContextAssembler`
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

Working path:

`TimeframeSyncEvent -> Wave1MtfContext -> MtfBarAlignmentStrategy -> StrategyIntent -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

## Experimental - next-stage seams implemented in the repository

The following seams exist in code and are covered by tests, but they are not first-class Wave 1 scope:

- `src/trading_core/context/`
  `TimeframeContextAssembler`, `ContextGate`, `BarAlignmentPolicy`, `ClosedBarPolicy`, `FreshnessPolicy`
- `src/trading_core/reconciliation/coordinator.py`
- `src/trading_core/recovery/classifier.py`
- `src/trading_core/positions/close_router.py`
- `src/trading_core/domain/reconciliation_extended.py`

These modules are implemented and usable, but they should be read as experimental next-stage prototypes rather than as the canonical active Wave 1 contour.

## Reserved - outside current scope

The following areas remain outside the repository's current implementation scope:

- governance layer
- multi-instrument orchestration
- multi-exchange orchestration
- derivatives / leveraged products
- full periodic / on-error reconciliation policy and governance decisions
- production execution adapter family

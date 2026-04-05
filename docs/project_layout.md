# Project Layout

This repository is organized around seam ownership, not around exchange adapters or deployment layers. The layout reflects both the active Wave 1 working contour and the implemented next-stage seams that already exist in the codebase.

## Top-level structure

- `CURRENT_STATUS.md` - active / experimental / reserved repository map
- `docs/spec/` - extracted source specification set
- `docs/implementation_status.md` - implementation status after remediation and seam work
- `src/trading_core/domain/` - canonical domain meaning and identity
- `src/trading_core/contracts/` - interface seams between packages
- `src/trading_core/input/` - normalized input and early context assembly
- `src/trading_core/strategy/` - strategy seam, including legacy single-bar and Wave 1 MTF reference strategies
- `src/trading_core/risk/` - risk verdict seam
- `src/trading_core/execution/` - order builder, guard, execution adapter, fill intake
- `src/trading_core/positions/` - fill-driven position truth and close routing
- `src/trading_core/portfolio/` - portfolio truth
- `src/trading_core/state/` - local persistence and state ownership
- `src/trading_core/reconciliation/` - startup reconciler plus reconciliation operating loop
- `src/trading_core/recovery/` - unknown-state classifier and system-mode transitions
- `src/trading_core/context/` - timeframe/context foundations
- `src/trading_core/governance/` - reserved governance/policy seam
- `tests/` - package, regression, and acceptance coverage

## Active Wave 1 contour

The active Wave 1 path currently uses:

- `src/trading_core/input/`
  with `Wave1MtfContextAssembler`
- `src/trading_core/strategy/`
  with `MtfBarAlignmentStrategy`
- `src/trading_core/risk/`
  with `ConfidenceCapRiskEvaluator`
- `src/trading_core/execution/`
  for builder, guard, adapter, and fill handoff
- `src/trading_core/positions/engine.py`
- `src/trading_core/portfolio/engine.py`
- `src/trading_core/state/`
- `src/trading_core/reconciliation/startup.py`

This is the working acceptance contour for the current core.

## Next-stage seams (experimental)

The following modules are implemented and test-covered, but they are not part of the Wave 1 active contour:

- `src/trading_core/context/`
  `TimeframeContextAssembler`, `ContextGate`, `BarAlignmentPolicy`, `ClosedBarPolicy`, `FreshnessPolicy`
- `src/trading_core/reconciliation/coordinator.py`
- `src/trading_core/recovery/classifier.py`
- `src/trading_core/positions/close_router.py`
- `src/trading_core/domain/reconciliation_extended.py`

These are experimental next-stage seams, not "missing code" and not mandatory Wave 1 behavior.

## Reserved areas

The following remain outside current scope:

- governance decision layer
- multi-instrument orchestration
- multi-exchange orchestration
- derivatives support
- full periodic / on-error reconciliation policy semantics
- production execution adapter family

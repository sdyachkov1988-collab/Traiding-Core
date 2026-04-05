# Trading Core

`Trading Core` is a Python 3.11+ implementation of a `Minimal Core v1` trading engine slice. The current repository already covers a full vertical path from a normalized market event through strategy, risk, order construction, execution boundary, fill-driven state updates, local persistence, and startup reconciliation.

## Current Status

Implemented packages:

- `Package A` - input and context foundation
- `Package B` - strategy decision boundary
- `Package C` - risk verdict boundary
- `Package D1` - order builder
- `Package D2` - pre-execution guard
- `Package E` - execution boundary via `MockExecutionAdapter`
- `Package F` - fill-driven spine with `Fill Processor`, `Position Engine`, and `Portfolio Engine`
- `Package G1` - state store via `JsonFileStateStore` with atomic writes
- `Package G2` - startup reconciliation

The current codebase supports a working path of:

`MarketEvent -> MarketContext -> StrategyIntent/NoAction -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

## Reserved For The Next Phase

The following seams are still intentionally reserved rather than active scope:

- full `TimeframeContext` family
- `Context Gate`
- periodic reconciliation
- on-error reconciliation
- governance layer
- unknown-state handling
- structured logging and broader observability hardening

These are visible in the spec and package map, but they are not yet unfolded as active implementation scope for the current slice.

## Running Tests

```bash
pytest
```

## Architectural Invariants

The current implementation follows these core engineering rules:

- `Decimal` is used for prices, quantities, and monetary values
- datetimes are UTC-aware
- domain objects are immutable dataclasses
- state snapshots are written atomically
- fill processing is idempotent within the current in-memory process scope

## Source Of Truth

The implementation is derived from the working spec set in:

- `docs/spec/index.md`
- `docs/implementation_status.md`
- `docs/project_layout.md`

# Implementation Status

## Current status

`Minimal Core v1` currently has a working vertical slice covering:

- `Package A` - Input and Context Foundation
- `Package B` - Strategy Decision Boundary
- `Package C` - Risk Verdict Boundary
- `Package D` - Order Builder and Pre-execution Guard
- `Package E` - Execution Boundary
- `Package F` - Fill-driven state spine
- `Package G` - State Store and Startup Reconciliation

In practical terms, the current repository supports the following phased path:

`MarketEvent -> MarketContext -> StrategyIntent/NoAction -> RiskDecision -> OrderIntent -> GuardOutcome -> AdmittedOrder -> ExecutionReport -> Fill -> Position -> PortfolioState -> PersistedStateSnapshot -> StartupReconciliationResult`

This document records implementation status only. It does not redefine the canonical model and does not upgrade temporary first-build choices into permanent invariants.

## Closed scope for Minimal Core v1

The following are currently considered closed for the first vertical slice:

- normalized input seam
- early strategy-facing context seam
- strategy decision seam
- separate risk verdict seam
- order construction seam
- pre-execution guard seam
- execution boundary as a single adapter-facing point
- internal fill-driven truth spine
- local state persistence
- startup-only reconciliation

## Reserved seams outside active scope

The following seams remain visible in the model but are not yet in active implementation scope:

- full `TimeframeContext` family
- `Context Gate`
- periodic reconciliation
- on-error reconciliation
- unknown-state family
- mature recovery coordinator
- protective close loop
- full `OrderState / ExecutionEvent` family
- full `Balance / AccountState` family
- governance-layer decisions

These remain reserved seams rather than missing code by accident. Their absence is phase-aligned with the current roadmap boundary.

## Assembly-level choices that are not canonical invariants

Some implementation details in the current slice are explicitly temporary assembly-level choices and must not be read as permanent core invariants.

Current examples:

- snapshot metadata records `accounting_policy = assembly_level_fee_in_cost_basis`
- `IdempotentFillProcessor` exists as a local protective implementation detail, not as a claim that the hardening layer is already complete
- first-build execution adapter behavior is represented by a mock boundary implementation, not by a mature production execution family

Rule of interpretation:

- if a behavior is needed to make the first slice work, that does not by itself make it contract-canonical;
- contract-level meaning still comes from the spec set in `docs/spec/`;
- hardening-layer obligations remain phase-scoped to later work even if early defensive code already exists.

## Wave 1G Acceptance Checklist

The current vertical slice should be checked against the following acceptance criteria.

### End-to-end path

- one `MarketEvent` can pass through the core path and contribute to `Position` and `PortfolioState`
- the path remains seam-separated across input, strategy, risk, order construction, guard, execution, fill, position, portfolio, state, and startup reconciliation

### Restart survivability

- local state can be persisted into the `State Store`
- restart can restore the latest local state snapshot
- restored state remains readable as local owned truth rather than reconstructed from strategy or execution assumptions

### Startup reconciliation

- startup reconciliation can compare local restored state with external startup basis
- the result is expressed as a formal startup reconciliation result
- startup reconciliation does not silently expand into periodic or on-error reconciliation behavior

### Boundary discipline

- execution boundary does not leak into strategy, risk, fill-driven state processing, or local persistence
- strategy does not read execution adapter details
- risk does not perform execution checks
- guard does not mutate state or replace execution
- state persistence does not replace reconciliation

## Next-document use

This status document is intended to support the next implementation phase by answering:

- what is already closed in the first vertical slice;
- which seams are intentionally still reserved;
- which current behaviors are temporary implementation choices;
- what should be validated before moving beyond `Minimal Core v1`.

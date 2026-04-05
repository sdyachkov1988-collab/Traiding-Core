# Project Layout

This repository is organized around seam ownership, not around exchange adapters or deployment layers. The layout now reflects both the closed Wave 1 core and the next-stage seams added during Tracks B and C.

## Top-level structure

- `docs/spec/` - extracted source specification set
- `docs/implementation_status.md` - current status after remediation and next-stage seam work
- `src/trading_core/domain/` - canonical domain meaning and identity
- `src/trading_core/contracts/` - interface seams between packages
- `src/trading_core/input/` - normalized input and early context assembly
- `src/trading_core/strategy/` - strategy seam, including legacy single-bar and Wave 1 MTF reference strategies
- `src/trading_core/risk/` - risk verdict seam
- `src/trading_core/execution/` - order builder, guard, execution adapter, fill intake
- `src/trading_core/positions/` - fill-driven position truth and close routing
- `src/trading_core/portfolio/` - portfolio truth
- `src/trading_core/state/` - local persistence and state ownership
- `src/trading_core/reconciliation/` - startup reconciler plus normal-loop reconciliation coordinator
- `src/trading_core/recovery/` - unknown-state classifier and system-mode transitions
- `src/trading_core/context/` - next-stage timeframe/context foundations
- `src/trading_core/governance/` - reserved governance/policy seam
- `tests/` - package, regression, and acceptance coverage

## How to read the layout

There are two important distinctions:

- `Minimal Core v1` is the closed Wave 1 vertical slice.
- Some Wave 2-style seams are already implemented in parallel because they were part of next-stage remediation work.

That means presence in the tree does not automatically mean “canonical active Wave 1 contour”.

## Active Wave 1 contour

The active Wave 1 path currently uses:

- input normalization
- phase-scoped `Wave1MtfContext`
- MTF-aware strategy
- risk
- builder
- guard
- execution
- fill-driven state spine
- local persistence
- startup reconciliation

This is the working acceptance contour for the current core.

## Implemented next-stage seams

The following directories now hold implemented next-stage capability:

- `src/trading_core/context/`
  contains canonical timeframe store, alignment/freshness policies, `TimeframeContextAssembler`, and `ContextGate`
- `src/trading_core/recovery/`
  contains unknown-state classification and safe-mode semantics
- `src/trading_core/reconciliation/`
  contains both startup reconciliation and the broader reconciliation operating loop
- `src/trading_core/positions/close_router.py`
  contains the position-originated close routing contour

## Boundary note

The repository intentionally keeps future seams visible, but we should read them carefully:

- full `TimeframeContext` exists, but Wave 1 active acceptance is still phase-scoped
- `ContextGate` exists, but is not treated as the mandatory Wave 1 contour
- close routing, unknown-state handling, and loop reconciliation are implemented as next-stage seams, not as proof that governance and full operational hardening are finished

# Implementation Status

## Current status

The repository now contains two layers of reality:

- a closed and remediated `Minimal Core v1` vertical slice;
- explicit next-stage seams from Tracks B and C that are present in code but not automatically promoted into the canonical Wave 1 contour.

Closed Wave 1 slice:

- `Package A` - normalized input and early context seam
- `Package B` - strategy decision boundary
- `Package C` - risk verdict boundary
- `Package D` - order builder and pre-execution guard
- `Package E` - execution boundary
- `Package F` - fill-driven state spine
- `Package G` - local state store and startup reconciliation

## Active acceptance path

The active acceptance path is now `MTF-first` and phase-correct for Wave 1:

`market input -> Wave1MtfContext -> MTF strategy -> risk -> builder -> guard -> execution -> fill -> position -> portfolio -> state -> startup reconciliation`

This is intentionally narrower than the full Wave 2 context family.

Meaning:

- the active path no longer uses the legacy single-bar strategy;
- the strategy receives `entry timeframe + mandatory HTF input` through the core;
- the active Wave 1 contour does not require full `TimeframeContext + ContextGate` canonization.

## Implemented next-stage seams

The following seams now exist in the repository as explicit next-stage capability:

- canonical timeframe store and `TimeframeContext`
- `ContextGate`
- unknown-state classification and system modes
- recovery coordinator with startup / periodic / on-error request modes
- position-originated close routing contour

These are implemented and test-covered, but they should still be interpreted through the roadmap boundary, not treated as if they were always part of the original Wave 1 contour.

## Track A and Track B remediation outcomes

The repository also reflects the completed remediation steps from Tracks A and B:

- risk sizing uses `reference_price` and step-aligned base sizing
- spot `SELL` requires a real current position basis
- impossible oversell is explicit conflict instead of silent clipping
- zero-quantity zombie positions are removed from portfolio truth
- builder rechecks quantity after post-rounding alignment
- acceptance uses a real execution-to-fill handoff helper
- fill idempotency covers fallback replay and restart restore bridge
- context/data integrity now includes:
  - history-depth warmup semantics
  - parent-period temporal alignment
  - monotonic timeframe updates
  - `source_event_time -> event_time`
  - early readiness guarding in strategy evaluation
- canonical datetime fields are now required to be UTC-aware

## Tolerance semantics

`SimpleStartupReconciler` defaults remain strict:

- `cash_tolerance = Decimal("0")`
- `quantity_tolerance = Decimal("0")`

Interpretation:

- `0` means exact `Decimal` equality;
- tolerance is not silently widened by default;
- any relaxed comparison must be chosen explicitly by the caller.

## Reserved or non-canonical interpretations

The following points remain important:

- full `TimeframeContext` is implemented, but not the only correct interpretation of Wave 1
- `ContextGate` exists, but is not the mandatory active Wave 1 contour
- hardening presence in code does not automatically make a behavior contract-canonical
- startup-only reconciliation semantics stay distinct from non-startup reconciliation semantics

## Wave 1G acceptance checklist

- one MTF-aware market input path reaches `Position` and `PortfolioState`
- restart restores persisted state
- startup reconciliation runs on restored state
- execution boundary does not leak into strategy, risk, or state ownership
- active acceptance path does not depend on the legacy single-bar strategy

## Practical reading rule

For current repository status:

- `README.md` is the quick summary
- this file is the working implementation snapshot
- the extracted source documents in `docs/spec/` remain the reference set for roadmap meaning

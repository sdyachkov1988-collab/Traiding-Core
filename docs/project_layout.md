# Project Layout

This repository is organized around architectural seams instead of vendor adapters or deployment concerns. The current layout reflects an implemented `Minimal Core v1` vertical slice, not just a placeholder skeleton.

## Top-level structure

- `docs/spec/` - working spec extracted from the source document set
- `docs/implementation_status.md` - current package status and Wave 1G acceptance checklist
- `src/trading_core/domain/` - canonical domain meaning
- `src/trading_core/contracts/` - implementation-facing seams
- `src/trading_core/input/` - Package A foundation
- `src/trading_core/strategy/` - Package B boundary
- `src/trading_core/risk/` - Package C boundary
- `src/trading_core/execution/` - Packages D, E, and fill intake for F
- `src/trading_core/positions/` - position truth layer for Package F
- `src/trading_core/portfolio/` - portfolio truth layer for Package F
- `src/trading_core/state/` - Package G1 state ownership and persistence
- `src/trading_core/reconciliation/` - Package G2 startup reconciliation seam
- `src/trading_core/governance/` - reserved external policy seam
- `tests/` - contract, invariant, and acceptance tests

## Why this layout

The layout mirrors the source specification set:

- the architecture and technical roadmap require load-bearing seams;
- the interface contracts require explicit boundaries;
- the implementation package document recommends package-oriented delivery;
- the governance and later reconciliation documents still remain visible even where they are not yet active implementation scope.

## Reserved Seams

The layout still keeps future seams visible without claiming they are already complete:

- full `TimeframeContext`
- `Context Gate`
- periodic/on-error reconciliation
- unknown-state handling
- governance decision layer
- mature protective close routing

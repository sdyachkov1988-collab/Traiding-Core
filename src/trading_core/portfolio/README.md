# Portfolio Layer

Purpose:

- maintain portfolio-level truth;
- track cash, equity, and realized PnL from fill-driven state updates;
- stay downstream from execution facts rather than upstream assumptions.

Current status:

- `SpotPortfolioEngine` is part of the active Wave 1 contour;
- portfolio updates reject contradictory fill / previous-position / resulting-position combinations;
- the domain layer enforces cash and position-map invariants for persisted truth.

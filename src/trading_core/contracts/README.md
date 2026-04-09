# Contract Layer

Purpose:

- define implementation-facing seams for the active `Minimal Core v1` contour and the implemented next-stage seam set;
- express boundaries in domain terms rather than vendor payloads;
- prevent direct coupling across strategy, risk, execution, and state.

Current coverage:

- normalized event input contract;
- Wave 1 MTF input seam contract;
- strategy contract for the current exported timeframe-based seam;
- risk contract;
- order construction, guard, execution, reconciliation, recovery, gate, and close-routing contracts.

Reading rule:

- Wave 1 contracts are the active first contour;
- Wave 2 contracts present here should be read as implemented next-stage seams, not as Wave 1 first-class interface obligations;
- the exported strategy contract should be read as the current implemented seam, not as proof that Wave 1 and Wave 2 contract harmonization is already closed;
- this package is not a claim that contract harmonization or governance integration is already complete.

# Contract Layer

Purpose:

- define implementation-facing seams for `Minimal Core v1`;
- express boundaries in domain terms rather than vendor payloads;
- prevent direct coupling across strategy, risk, execution, and state.

Current coverage:

- normalized event input contract;
- Wave 1 MTF input seam contract;
- strategy contract;
- risk contract;
- order construction, guard, execution, reconciliation, recovery, gate, and close-routing contracts.

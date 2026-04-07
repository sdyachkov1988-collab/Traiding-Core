# Domain Layer

Purpose:

- hold canonical domain objects and value semantics;
- preserve the distinction between intent, order, execution facts, and accounting truth;
- avoid transport-specific or adapter-specific leakage.

Current coverage:

- market event primitives;
- strategy intent primitives;
- risk decision primitives;
- order intent and execution fact primitives;
- portfolio, persisted-state, timeframe, gate, reconciliation, recovery, and close-routing primitives.

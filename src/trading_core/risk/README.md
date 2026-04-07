# Risk Layer

This package implements `Package C`.

Responsibilities:

- evaluate upstream strategy-side intent;
- return a separate `RiskDecision`;
- avoid direct order submission or state mutation ownership.

Current status:

- `ConfidenceCapRiskEvaluator` is part of the active Wave 1 contour;
- risk sizing uses `reference_price` and floor alignment by step;
- intent / instrument-basis mismatch is rejected explicitly.

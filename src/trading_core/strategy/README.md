# Strategy Layer

This package implements `Package B`.

Responsibilities:

- accept valid market/context input from the input layer;
- produce `StrategyIntent` or explicit no-action;
- avoid risk, execution, and accounting concerns.

Current status:

- `MtfBarAlignmentStrategy` is the active Wave 1 strategy seam;
- `BarDirectionStrategy` remains available as reference-only legacy behavior.

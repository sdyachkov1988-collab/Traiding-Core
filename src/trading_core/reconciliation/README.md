# Reconciliation Layer

Purpose:

- hold startup and later normal-loop reconciliation seams;
- compare local and external truth without redefining domain meaning;
- support later recovery and unknown-state handling.

Current status:

- `SimpleStartupReconciler` is part of the active Wave 1 contour;
- startup reconciliation keeps strict default tolerances and does not hide shared mismatch behind zero-quantity pruning;
- `RecoveryCoordinator` is implemented as the Wave 2D reconciliation-loop seam;
- the reconciliation loop formally supports `startup`, `periodic`, `on-error`, and `operator-command` trigger paths;
- conflicting outcomes block new actions through formal recovery posture transitions rather than ad hoc flags.

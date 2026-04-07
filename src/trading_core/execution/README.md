# Execution Layer

Purpose:

- keep execution behind interfaces;
- isolate adapter-facing logic from core domain meaning;
- preserve the distinction between order submission, observed order state, and execution facts.

Current status:

- `SimpleOrderIntentBuilder` and `SimplePreExecutionGuard` are part of the active Wave 1 contour;
- execution adapters and fill handoff are implemented for the acceptance slice;
- builder logic now uses true step-multiple alignment and validates close-route instrument coherence.

# State Layer

Purpose:

- provide a single source of truth for owned state;
- support atomic writes and survivability constraints;
- stay aligned with the guardrails document.

Current status:

- `JsonFileStateStore` is part of the active Wave 1 contour;
- persisted snapshots are written atomically;
- save/load now validate portfolio invariants instead of accepting contradictory state silently.

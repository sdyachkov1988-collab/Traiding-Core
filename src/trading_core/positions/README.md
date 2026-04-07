# Position Layer

Purpose:

- hold position-side truth derived from execution facts;
- support protective close logic through a separate close-routing seam;
- remain separate from strategy intent and order submission.

Current status:

- `SpotPositionEngine` is part of the active Wave 1 contour;
- position updates reject cross-instrument fill corruption and impossible oversell;
- `CloseIntentRouter` is implemented as the Wave 2E close-routing seam.

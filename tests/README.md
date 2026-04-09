# Tests

Current test categories:

- contract tests for interface seams;
- invariant tests from the guardrails document;
- execution boundary tests with mock adapters;
- dedicated `Wave 1G` acceptance slice tests for `Minimal Core v1` in `tests/test_acceptance_wave1g_minimal_core.py`;
- Wave 2 seam tests for context, recovery, reconciliation loop, and close routing;
- targeted regressions for the Wave 1 / Wave 2 critical-fix cases.

Reading rule:

- this suite does not claim that Wave 3 hardening is already covered;
- Wave 2 seam tests confirm implemented seam behavior, not full canonical/governance closure of those seams;
- close-routing tests should be read as seam coverage, not as proof that all contract ambiguities around protective close flow are already harmonized.

Current suite status: `239 passed`

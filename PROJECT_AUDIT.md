# Project Audit — Copilot Instructions (snapshot 2025-12-18)

## Purpose
Short audit capturing the current structure, findings from validation, risks, and prioritized remediation actions to make the project easy to use and maintain.

## Current state (summary)
- Core artifacts: `copilot-instructions/COPILOT_INSTRUCTIONS.md`, `copilot-instructions/COMMANDS.md`, `copilot-instructions/templates/*` (schemas), `tools/plan_rhythm.py`, `tools/run_checks.py`, `tools/act_policy.py`.
- Story planner, checkers, and automated suggestion/apply flows are implemented and unit-tested (some tests added under `tests/`).
- Copilot behavior updated: simulation-first model (Copilot simulates checks and planner flows and will not execute `.py` scripts on the user's machine by itself).
- Default tonal architecture: Tone.md 7-act distribution implemented; planner and checks updated accordingly.

## Key findings (validation)
- Consistency: Documentation and `COMMANDS.md` and `COPILOT_INSTRUCTIONS.md` consistently assert simulation-first behavior. Good.
- Missing helper: `tools/cpctl.py` helper CLI planned but not implemented (todo #2).
- Missing scaffolding: `story/chapters/*` files are largely missing; this produces act_missing_chapter warnings when running checks (story-level issue, but affects example runs and tests).
- Tests: Unit tests exist for some functions; pytest is not installed by default; tests that check planner behavior are present. Suggest adding E2E simulation tests (todo #3).
- README: references simulated runs; quick reference could be enhanced to point to `COMMANDS.md` (todo #1 done/in-progress)
- Artifacts & audit trail: `story/suggestions/` and `story/continuity/` used for artifacts; revision_history is appended when files are modified.

## Prioritized recommendations
1. Implement `tools/cpctl.py` (safe simulator wrapper) and unit tests (todo #2). This will make the simulated workflows easier for contributors.
2. Add end-to-end simulation tests that cover planner → apply → simulated-check and assert expected artifacts (todo #3).
3. Scaffold minimal chapter JSON + part files (chap-01..chap-12) so simulated checks are meaningful and warnings are reduced (todo #4 and #8).
4. Add `PROJECT_AUDIT.md` (this file) and a short `CONTRIBUTING.md` with developer Quickstart (install pytest, run tests, run scripts locally, how to request Copilot to simulate vs run locally) (todo #7).
5. Propose an example CI gating policy (todo #9) describing which checks you want to promote to error-level for CI.
6. Cleanup & consolidate docs to eliminate duplication and ensure consistent language across `COPILOT_INSTRUCTIONS.md`, `COMMANDS.md`, and `README.md` (todo #10).

## Low-risk housekeeping
- Normalize `act_level_rhythm` enums and document mapping for custom labels (done).
- Add small scaffolding scripts or templates for generating chapter stubs.

## Next actions (I will take them if you approve)
- Implement `tools/cpctl.py` as a safe, simulation-only CLI and add tests (start immediately). (Assigned to todo #2)
- After cpctl is in place, optionally scaffold chapter files (chap-01..chap-12) and add E2E simulation tests. (Todos #4 & #3)
- Add `CONTRIBUTING.md` with dev quickstart (todo #7).

---

If this audit looks good, I will proceed to implement `tools/cpctl.py` and add the tests (marking todo items as in-progress/completed as I go).
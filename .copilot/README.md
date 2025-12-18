# Copilot Local Artifacts (DEPRECATED)

The local assistant agent approach (tools/assistant_agent.py and .copilot/requests/) has been deprecated and removed from active use.

Current workflow
- Copilot now performs simulated runs of the full-check, iterative rewrite, and assessment flow in-repo and writes artifacts under story/continuity/ and story/rewrites/. These simulations are deterministic and intended to support rapid iteration without requiring local agents or background services.
- If you previously used the local agent, you can remove any remaining agent files. Actual execution on your machine can still be done manually by running tools/run_checks.py --full.

Notes
- This file replaces the earlier agent instructions to avoid confusion.

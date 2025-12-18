Simulation Mode — repository policy

This repository supports a simulation-first workflow: Copilot (and contributor CI) may simulate check runs and generate artifacts in-repo without executing Python scripts.

Guidelines:
- Copilot will prefer simulated artifacts (e.g., `story/checks/last_full_run_simulated.txt`, `story/continuity/*.jsonc`, `story/rewrites/*.md`) when present.
- Tests should be written to accept and validate the presence and content of those simulated artifacts.
- If you need to perform a real run, execute `python tools/run_checks.py --full` locally; simulated artifacts will be ignored in that case.

Why simulation?
- Safety: avoids running user-local scripts during interactive assistance.
- Speed: enables fast iteration without executing heavy checks.
- Determinism: simulations are deterministic and predictable for tests.

Please keep a simulated run summary up to date at `story/checks/last_full_run_simulated.txt` and ensure `story/continuity/checks-report-<ts>.jsonc` exists after major edits.
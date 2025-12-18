# Copilot Command Reference — Simplified

NOTE: All commands are *simulated* by Copilot. Copilot does not execute repository scripts on the user's machine; it presents simulated artifacts and the exact local commands you can run.

Quick command list (exact keywords users should use)
- plan-rhythm — Simulate planner and produce `story/tone_plan.jsonc` and `story/act_plan.jsonc` (dry run). Example: "plan-rhythm (dry run)"
- apply-suggestions — Apply planner metadata suggestions (with explicit confirmation). Example: "apply-suggestions chap-05..chap-08"
- run-checks — Simulate the full validation pass and return a checks summary. Example: "run-checks (full)"
- generate-outline — Produce a chapter outline + suggested metadata. Example: "generate-outline chap-05, 1500-2000 words, tone: dread"
- rewrite — Propose iterative rewrite drafts for a chapter (not applied without permission). Example: "rewrite chap-03 up to assessment threshold (do not apply)"
- status / show-plan / show-reports — Query current artifacts. Example: "show-plan" or "show last checks report"

Command categories (how to think about commands)
- Planning: plan-rhythm, show-plan
- Validation: run-checks, show-reports
- Application (metadata edits): apply-suggestions, scaffold
- Generation: generate-outline, rewrite
- Info & governance: status, help, commands

Keywords (short list users can include in prompts)
- dry run, simulate, preview
- apply, confirm, force (requires explicit confirmation)
- full, partial, chapter:<NN>, range:<NN-NN>
- tone:<word>, act:<id>, chapter_level_rhythm:<Expectation|Disruption|PartialResolution>

What Copilot will do (for each keyword)
- simulate/dry run: compute outputs and present simulated artifact content (JSON-style summaries). Does not write files unless the user explicitly asks Copilot to edit repository files.
- apply/confirm: after explicit confirmation, Copilot will perform in-repo metadata edits (chapter JSON updates) and write `apply-results-<ts>.jsonc` and `revision_history` entries.
- full: use the whole book (chapters_per_book, act_distribution) when computing plans or checks.
- partial/chapter/range: restrict simulated actions/checks to the given chapters or range.

Exact local commands (what Copilot will tell the user to run locally)
- Planner (real): python tools/plan_rhythm.py [--annotate-suggestions] [--apply]
- Full checks (real): python tools/run_checks.py --full
- Tests (real): python -m pytest -q

Safety & consent (short)
- Copilot will never run `.py` scripts on your machine.
- Copilot can *simulate* runs and will produce artifacts for review.
- Copilot will only edit files (apply-suggestions or rewrite) after explicit confirmation.

Examples (user → Copilot expected behavior)
- "plan-rhythm (dry run)" → Copilot: returns a simulated `tone_plan` table and suggested `act_plan`.
- "apply-suggestions chap-05..chap-08" → Copilot: asks for confirmation and then applies metadata edits (if allowed), writes `apply-results-<ts>.jsonc`, and simulates a follow-up check.
- "run-checks (full)" → Copilot: returns a simulated `checks_report` summary and top N issues.

End of file.
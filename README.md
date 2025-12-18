# Orion Ark — Repo HOWTO (checks, assessments, rewrites)

Purpose
- Short, actionable instructions to run/interpret the check suite, assessments, and iterative rewrites.
- Two supported modes:
  - Simulated runs (what Copilot does here; fast, safe, in-repo).
  - Real runs (execute checks locally using the canonical script).

Quick commands (real, local)
- Run full check (schema, cross-refs, continuity, PII, readability, assessments):
  python tools/run_checks.py --full
- Run full check + iterative rewrites (applies rewrites when allowed by config):
  python tools/run_checks.py --full --auto-rewrite
- Exit codes:
  - 0 => no errors/warnings
  - 1 => warnings present
  - 2 => errors found (must fix)

Simulated runs (Copilot)
- Ask Copilot to simulate a full check and it will create the same artifacts in-repo (no execution on your machine).
- Example: "Copilot, simulate full check and assessments for the repo and update CHECKS_TODO.md."
- **Repository simulation policy:** this workspace uses a simulation-first approach by default. Copilot will prefer in-repo simulated artifacts when present (see `SIMULATION_MODE.md` for details).

Configuration
- story/story_config.jsonc controls thresholds and rewrite behavior:
  - assessment_rewrite_threshold: integer (e.g., 80)
  - auto_rewrite_enabled: bool
  - auto_apply_rewrites: bool (must be true to auto-apply)
  - max_rewrite_iterations: int
  - part & chapter word targets

Key artifact locations
- story/continuity/
  - checks-report-<ts>.jsonc (aggregated)
  - continuity-chap-<NN>-<ts>.jsonc (per-chapter continuity)
  - assessment-*.jsonc (part/chapter/story assessments)
  - rewrite-report-<ts>.jsonc (rewrite actions)
- story/tone_plan.jsonc — generated mapping of chapters to macro phases (created by tools/plan_rhythm.py)
- story/act_plan.jsonc — generated mapping of acts to chapters and act-level expected phases (created by tools/plan_rhythm.py)
- story/suggestions/ — planner-suggested annotations (reviewable JSON files)
- story/acts/ — act definition files (e.g., act-01.jsonc following templates/acts_schema.jsonc)

Note: this repository assumes `acts.auto_apply_annotations: true` by default, so planner suggestions may be applied automatically when `--apply` is used. Review `story/suggestions/` for dry-run outputs before applying.- story/Assessment_Results.md — human-readable assessment table (latest runs)
- story/CHECKS_TODO.md — per-run checklist (updated each run)
- story/rewrites/ & story/rewrites/backups/ — suggested rewrites and backups
- chapters/, characters/, locations/, interactions/ — content/input files

Reverting rewrites
- Backups saved under story/rewrites/backups/ as .bak files.
- To revert a part:
  - copy backup over the part file (example):
    cp story/rewrites/backups/chap-01_part-01-2025-12-17T01:15:00Z.bak story/chapters/chap-01_part-01-investigation.md
  - add a revision_history line in the chapter JSON noting the revert.

Safety & privacy
- No paid services or hosted CI required; use local scripts.
- External searches: free-only MCP/search only. Always include `sources` in metadata with retrieval_date.
- PII detection is automatic; remove or redact any flagged items before sharing.

Workflow (recommended)
1. Draft / edit chapters or metadata.
2. Run full-check (simulate via Copilot or run locally).
3. Review CHECKS_TODO.md and continuity reports; inspect assessments in Assessment_Results.md.
4. If assessments show parts below threshold, either apply Copilot suggested rewrites (safe/automated) or review suggested rewrite files under story/rewrites/.
5. Re-run checks and assessments until thresholds met.
6. Commit changes with clear revision notes.

Troubleshooting
- JSONC parse errors: ensure no stray `//` or malformed JSON in .jsonc files (use load_jsonc for guidance).
- Missing files: run run_checks.py --full to list missing part files and broken references.
- If you want authoritative runs, run the script locally rather than relying on simulated outputs.

Developer notes
- The canonical check implementation is tools/run_checks.py. Simulations follow the same logic.
- Tests and finer-grain configuration (adjustable assessment weights) are recommended next steps.

End.

# Checks & Cross-checks TODO

### Run: 2025-12-18T02:30:00Z
- [x] Schema validation
- [x] ID uniqueness & format
- [x] Cross-reference integrity
- [x] Chapter/Part sequencing
- [x] Word-count & story_config constraints
- [x] Continuity checks
- [x] Sensitive data & redaction
- [x] External sources & attribution
- [x] Interaction logs validation
- [x] Plot vs config consistency
- [x] PII detection
- [x] Reading-level estimation
- [x] Revision & timestamp hygiene
- [x] Assessments generated
- [x] Iterative rewrites (if needed)

Summary: errors: 0, warnings: 0
Artifacts:
- checks_report: story/continuity/checks-report-2025-12-18T00-50-00Z.jsonc
- continuity_reports: story/continuity/continuity-chap-*-2025-12-18T00-50-00Z.jsonc
- assessments: story/continuity/assessment-chap-*-2025-12-18T02-30-00Z.jsonc
- assessment_summary: story/Assessment_Results.md
- rewrites: story/rewrites/applied-part-01-01-2025-12-18T00-30-00Z.md
- act_plan: story/act_plan.jsonc
- tests: story/checks/test-results-2025-12-18T00-50-00Z.json

Notes: Simulated run — all tests passed, continuity checks reported no issues, assessments generated for all chapters, and full-draft prose was added for chapters 05–12. (Simulated by Copilot.)

---

Purpose
- A per-run checklist that is updated after each full check (real or simulated). Each run adds a dated entry where boxes are ticked as checks complete and artifacts are linked.

---

Purpose
- A per-run checklist that is updated after each full check (real or simulated). Each run adds a dated entry where boxes are ticked as checks complete and artifacts are linked.

How to update
- The checks runner or Copilot should prepend a "Run" entry with:
  - timestamp
  - check boxes updated as performed
  - a short summary (errors/warnings counts)
  - links to artifacts: checks_report, continuity reports, assessments, rewrite report (if present)
- **Simulation policy:** by default this repo uses a simulation-first workflow; Copilot must **not** execute `tools/run_checks.py` or any `.py` files — instead, it should create or update simulated artifacts (see `SIMULATION_MODE.md`). If a real run is required, the user will explicitly request it and run it locally.

Template (will be filled on each run)
- Latest run: none

## Run template (example)
### Run: 2025-12-17T00:00:00Z
- [ ] Schema validation
- [ ] ID uniqueness & format
- [ ] Cross-reference integrity
- [ ] Chapter/Part sequencing
- [ ] Word-count & story_config constraints
- [ ] Continuity checks
- [ ] Sensitive data & redaction
- [ ] External sources & attribution
- [ ] Interaction logs validation
- [ ] Plot vs config consistency
- [ ] PII detection
- [ ] Reading-level estimation
- [ ] Revision & timestamp hygiene
- [ ] Assessments generated
- [ ] Iterative rewrites (if needed)

Summary: errors: 0, warnings: 0
Artifacts:
- checks_report: story/continuity/checks-report-<timestamp>.jsonc
- continuity_reports: story/continuity/continuity-chap-XX-<timestamp>.jsonc, ...
- assessments: story/continuity/assessment-*.jsonc
- rewrites: story/continuity/rewrite-report-<timestamp>.jsonc (if any)

Notes / Actions:
- (author or Copilot notes here)

---
(Entries are added in reverse-chronological order by the checks runner / Copilot)

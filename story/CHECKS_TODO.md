# Checks & Cross-checks TODO

Purpose
- A per-run checklist that is updated after each full check (real or simulated). Each run adds a dated entry where boxes are ticked as checks complete and artifacts are linked.

How to update
- The checks script (tools/run_checks.py) or Copilot should prepend a "Run" entry with:
  - timestamp
  - check boxes updated as performed
  - a short summary (errors/warnings counts)
  - links to artifacts: checks_report, continuity reports, assessments, rewrite report (if present)

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

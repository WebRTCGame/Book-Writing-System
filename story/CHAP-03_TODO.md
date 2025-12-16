# Chapter 03 — TODO & Plan

Meta
- id: todo-chap-03
- chapter: chap-03
- owner: copilot
- created: 2025-12-17T00:00:00Z
- acceptance: chapter-level story_quality >= story_config.assessment_rewrite_threshold (default 80)

1) Objectives
- Continue investigation arc: follow-up to beacon/probe; raise stakes and tension.
- Introduce new scene(s) / characters if needed (e.g., contact, informant, secondary antagonist).
- Produce 2 parts (Part 1: Approach / Discovery; Part 2: Confrontation / Cliffhanger).
- Ensure POV, continuity, and metadata consistent with schemas.

2) Deliverables (files to create/update)
- story/chapters/chap-03_part-01-approach.md (800–1200 words)
- story/chapters/chap-03_part-02-confrontation.md (800–1200 words)
- story/chapters/chap-03.md (combined, headers)
- story/chapters/chap-03.jsonc (chapter metadata + parts array)
- story/characters/char-xxxx.jsonc (if new character(s) needed)
- story/locations/loc-xxxx.jsonc (if new location(s) needed)
- story/interactions/int-xxx.jsonc (representative interaction)
- story/continuity/rewrite-report-...jsonc (if rewrite applied)
- story/continuity/assessment-chap-03-<ts>.jsonc & part-level assessments
- story/continuity/checks-report-<ts>.jsonc

3) Steps & Commands
- Outline: "Create chap-03 outline using chapter_schema.jsonc. 2 parts. POV Aya. Word targets per part 800–1200."
- Create character/location logs if needed using character_schema.jsonc / location_schema.jsonc.
- Generate prose for part-01 and part-02 (follow story_config: tone, reading_level, default_pov).
- Create combined chap-03.md and chap-03.jsonc with parts array, beats, estimates.
- Run full checks: `python tools/run_checks.py --full`
- Generate assessments (implicit in --full). Inspect story_quality for chapter and parts.
- If any part/chapter < story_config.assessment_rewrite_threshold:
  - If config.auto_rewrite_enabled and auto_apply_rewrites true → iterative auto-rewrite loop will run (backups created).
  - Otherwise Copilot will produce suggested rewrites under story/rewrites/ and await approval.
- Re-run full checks and re-assess until chapter meets threshold or max iterations reached.

4) Prompts samples (for Copilot)
- "Create chap-03 outline (2 parts, Aya POV, 800–1200 words per part). Return chapter_schema and a 3-bullet beat list."
- "Write chap-03_part-01 (Aya POV, tense/atmospheric, 900 words). Follow plot: approach to probe coordinates, discovery and hint of danger."
- "Run full checks and assessments for chap-03; return checks_report and assessment files, and list any chapters below threshold."

5) Acceptance Criteria
- All JSONC artifacts validate (schema).
- continuity_report.jsonc has zero error-level contradictions for chap-03.
- chapter-level assessment story_quality >= story_config.assessment_rewrite_threshold (default 80).
- If auto_apply_rewrites is false: suggested rewrites exist under story/rewrites/ for any failing part.

6) Notes & Safety
- Copilot will not apply destructive changes without permission unless auto_apply_rewrites:true in story_config.jsonc.
- All applied rewrites will be backed up under story/rewrites/backups/ and logged in chapter revision_history.

Status
- [x] Outline created
- [x] Parts written: chap-03_part-01-approach.md, chap-03_part-02-confrontation.md
- [x] chapter file and metadata created (chap-03.jsonc)
- [x] Supporting character (Lyra Moss) added
- [x] Interaction log added (int-aya-elya-01.jsonc)
- [x] Full-check requested via local agent (.copilot/requests/runchecks-full-autorewrite-2025-12-17T03:30:00Z.jsonc)
- [x] Initial checks/assessments completed and chapter meets threshold (see story/continuity/)
- [x] Next actions: small phrasing pass and prepare chap-04 outline.

End.

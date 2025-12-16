# Copilot Instructions for Writing a Fiction Book

## Table of contents
- Purpose & scope
- Audience & roles
- Prompt structure (system / context / request)
- Output formats & schemas
- Logging & naming conventions
- Continuity and QA checks
- External resources & MCP/search guidance
- Versioning & workflow
- Security, privacy & redaction
- Automation, linting & CI
- Quick reference & examples
- Appendix: templates
- Checks, validation & CI
- Assessment & scoring

## Purpose & scope
Provide precise, repeatable guidelines and schemas for using Copilot (or similar assistants) to author, log, and maintain a fiction manuscript and its metadata. This is intended for single authors, writers’ rooms, and technical workflows that require coherent, auditable metadata and reproducible content generation.

## Audience & roles
- Author: writes scenes and approves changes.
- Editor: reviews style, continuity, and finalizes chapters.
- Copilot/Assistant: performs generation, logging, and checks following these rules.
- Automation: CI/linting tools that validate JSON, IDs, and continuity reports.

## Prompt structure (must follow)
Always use a 3-part structure:
1. System message — role, constraints, output rules (strict format: "Output must follow <schema> or <format>").
2. Context — attach relevant, minimal logs or JSON objects (character, location, chapter metadata) and only the most recent prose needed.
3. Request — single clear task, including output format (exact schema file name) and constraints (word count, POV, tense).

Example system message:
"You are a fiction-writing assistant. Respond only in the requested format. Preserve continuity; include ISO8601 timestamps on all created/updated objects; never invent an ID format—use short-kebab. If you use external sources, populate `sources` with attribution."

## Output formats & schemas
- Machine logs: JSONC files in templates/ with exact field names. Use the provided schemas (character_schema.jsonc, location_schema.jsonc, chapter_schema.jsonc, interaction_schema.jsonc, continuity_report.jsonc).
- Prose: store raw narrative in plain text or markdown (`chapters/chap-XX.md`) and reference in chapter metadata.
- Always include `id`, `last_updated`, and `revision_history` for mutable objects.

## Logging & naming conventions
- ID format: short-kebab, prefixed by type (e.g., char-lena-sato, loc-east-docks, chap-03).
- Timestamps: ISO8601 Zulu (e.g., 2025-12-16T14:30:00Z).
- Revision history entry: { date, author, note }
- Tags: lowercase single words for filtering.
- Minimally invasive updates: for "update" requests include only changed fields.

## Continuity & QA checks
Request a "continuity report" to surface:
- Contradictions between character attributes and prose (e.g., age or scars).
- Missing references (a referenced character not in logs).
- POV or tense deviations.
- Unlinked items (objects or clues not referenced by chapters).
Report format: continuity_report.jsonc (see templates).

Automated checks (recommended):
- JSON schema validation for all logs.
- ID uniqueness across logs.
- Cross-reference integrity (e.g., chapter.pov_character_id exists in characters).

## External resources & MCP/search guidance
- If you are allowed to query an MCP or search service:
  - Use only free, public, or otherwise authorized MCP/search endpoints that do not require paid subscriptions. Do NOT use paid services.
  - Always add a `sources` array: { name, url, summary, retrieval_date }.
  - Cache retrieved snippets and record retrieval timestamps.
  - Mark any content derived from external sources with `source_attribution`.
- If external resources are not available or require payment, return `sources: []` and continue with best-effort internal reasoning.

## Versioning & workflow
- Chapter `status`: draft / revised / final.
- Use small, reviewable edits (target <500–1000 words per edit).
- Keep a `revision_history` on important objects with succinct notes (like commit messages).
- Consider using a branch-per-arc or branch-per-act in source control for major revisions.

## Security, privacy & redaction
- Do NOT include any real personal data unless explicitly authorized.
- Mark potentially sensitive content in metadata (e.g., `sensitive: true`) and redact or obfuscate as required by policy.
- If the story uses real-world persons, include consent metadata or replace with fictional analogues.

## Automation, linting & CI
- Do NOT assume or require hosted CI services (e.g., GitHub Actions) or any paid tooling. Use local scripts, pre-commit hooks, or self-hosted runners that do not incur paid service costs.
- Recommended: run checks locally or via self-hosted automation that you control. The checks described in "Checks, validation & CI" should be runnable offline or on free infrastructure.
- When documenting external queries, ensure every retrieval includes attribution and retrieval_date and is cached for reproducibility.

## Best practices
- Be explicit about POV, tense, voice, and length in every generation prompt.
- Ask for short, testable outputs (structured JSON + short prose examples).
- Keep single-purpose prompts (create, update, summarize, check).
- Require explicit author approval for any metadata changes beyond minor edits.

## Quick reference & sample prompts
- "Create character using character_schema.jsonc. Provide one-paragraph sample scene separate from the JSON."
- "Update char-xxx: set current_state to 'interrogating captain' and add tag 'on-mission'. Return updated JSON only."
- "Generate chap-03 outline (500–800 words, present tense, Lena POV); return chapter_schema and outline markdown."

## Plot file (story/plot.md) and continuous updates
- Purpose: maintain a single, up-to-date synopsis with short chapter summaries, an arc summary, and tracked open threads for planning and continuity.
- Location & format: story/plot.md (Markdown). The file must begin with a machine-readable JSONC metadata block (fenced ```jsonc) containing:
  - id, title, last_updated (ISO8601), chapters (array of {id, title, summary, first_written, last_updated}), arc_summary, open_threads (array), revision_history (array of {date, author, note}).
- Human-readable section: after the metadata, include a short TL;DR, an "Arc summary" paragraph, "Chapters" with 1–3 sentence summaries per chapter, and "Open threads".
- Update rules (must follow):
  1. On chapter creation: append a chapter object to metadata.chapters and a matching bullet in the human-readable section; update last_updated and add a revision_history entry.
  2. On chapter edits: update that chapter's summary and last_updated in both metadata and prose; push a revision_history entry describing the change.
  3. On major plot changes: update arc_summary and open_threads to reflect new direction.
- Content constraints: chapter summaries should be 20–70 words; arc_summary 1–3 sentences; open_threads are short, actionable items.
- Example prompt: "Update story/plot.md: add summary for chap-04 (40–60 words) and update arc_summary to mention the watching process. Return the updated plot.md only."
- Validation: treat the JSONC block as authoritative for machine checks (CI should validate JSON schema and cross-check chapter IDs exist in chapters/*.jsonc).

## Story configuration (story/story_config.jsonc)
- Purpose: central, machine-readable story settings that guide generation and validation (chapter length, character counts, reading level, whether the book is part of a series, expected number of chapters, etc.).
- Location & format: story/story_config.jsonc (JSONC). Copilot should read this file before bulk generation tasks (e.g., creating multiple chapters or casting characters).
- Recommended fields:
  - id, title, language, main_genre, subgenres
  - is_series (bool), books (int), chapters_per_book (int)
  - min_chapter_words, max_chapter_words, chapter_word_target
  - expected_characters_min, expected_characters_max, plot_lines
  - complexity (low/medium/high), reading_level (e.g., grade_10), default_pov, tone
  - plot_file: path to story/plot.md
  - last_updated, revision_history
- Example prompt: "Read story/story_config.jsonc and generate 3 chapter outlines following its chapter_word_target and complexity. Return chapter_schema JSONC objects only."

## Chapter parts & sequencing
- Purpose: Break chapters into discrete parts (scene-level or plot-line fragments) to support parallel plotlines, easier revisions, and granular continuity tracking.
- Naming convention (recommended): Use zero-padded chapter and part numbers and an optional plot-line slug:
  - story/chapters/chap-01_part-01-beacon.md
  - filesystem sort order must reflect reading order.
- Per-part metadata: Each chapter should include a `parts` array in its chapter_schema.jsonc. Each part object must have:
  - id (e.g., "chap-01-part-01")
  - sequence (integer, 1-based)
  - file (relative path to the part's prose file)
  - title (optional short title)
  - plot_lines (array of plot-line ids or slugs)
  - summary (20–70 words)
  - beats (array of beat ids/summaries used in that part)
  - estimated_word_count and actual_word_count
  - status (draft / revised / final)
- Workflow rules:
  1. On "split" requests: create new part files and append parts to chapter_schema.parts. Ensure `sequence` and filenames maintain order.
  2. On edits: update the part's summary, word counts, last_updated, and chapter revision_history.
  3. When plot-lines change: update affected part.plot_lines and summaries; add a revision entry documenting the change.
- Continuity & validation:
  - Ensure parts' sequences are contiguous starting at 1 and files exist.
  - Validate that each part references valid plot_line ids and beat ids.
  - CI should verify filename sequence ordering and cross-reference part files with chapter_schema.parts.
- Prompt pattern (example):
  - "Split chap-01 into 2 parts across plot-lines 'beacon' and 'watch'. Create files chap-01_part-01-beacon.md and chap-01_part-02-watch.md, each 300–600 words. Return parts metadata (JSON) and short 30–50 word summaries."

## Checks, validation & CI

Purpose
- Define a standard, machine-actionable checklist and reporting format for validating story artifacts (schemas, chapters, characters, locations, plot, parts) and for surfacing continuity, cross-reference, and policy issues.

When to run
- On every relevant change (chapter/part metadata, character/location edits, plot.md updates), and as a gated CI step before merging.

Severity levels
- error: must-fix (CI fails).
- warning: likely issue; surface to author (CI warns).
- info: informational only.

Core checks (machine-actionable)
- Schema validation
  - Validate all JSONC files in templates/ and story/ against their schemas (character_schema, chapter_schema, location_schema, interaction_schema, continuity_report).
  - Output: file-level schema errors (file, pointer, message).
- ID uniqueness & format
  - Ensure all ids follow short-kebab and are unique across the story (chars, locs, chaps, parts, interactions).
  - Output: duplicate id list.
- Cross-reference integrity
  - Verify referenced IDs exist (chapter.pov_character_id in characters, chapter.setting_location_id in locations, part.plot_lines exist in plot.md plot_lines, part.files exist).
  - Output: broken references with suggested fixes.
- Chapter/Part sequencing
  - Confirm chapter.parts sequences are contiguous (1..N) and filenames sort in reading order (zero-padded).
  - Output: mis-sequenced parts, missing files.
- Word-count & story_config constraints
  - Check actual_word_count and estimated_word_count against story_config: chapter_word_min/target/max and part_word_target_min/max.
  - Output: out-of-range chapters/parts.
- Continuity checks
  - Detect contradictions (e.g., character described with scar in char log but 'clean face' in chapter), missing references (character used in prose but not in cast list), inconsistent first_appearance_chapter, or location inhabitant mismatches.
  - Output: continuity_report.jsonc per chapter (see templates/continuity_report.jsonc schema).
- Sensitive data & redaction
  - Ensure secrets with redacted:true are not present in prose or public metadata; flag any likely real-person data.
  - Output: found sensitive snippets (file, snippet, recommended redaction).
- External sources & attribution
  - Confirm external research/sources fields exist for any content that used MCP/search; check `sources` arrays for name/url/retrieval_date.
  - Validate source URLs look well-formed and include retrieval_date.
- Interaction logs validation
  - Verify interactions reference valid participants (characters) and referenced chapters/locations exist.
  - Output: invalid interaction entries.
- Plot vs config consistency
  - Validate story/plot.md chapters count and plot_lines list against story/story_config.jsonc (e.g., chapters_per_book, expected plot_lines count).
  - Output: mismatches with recommendations.
- PII & sensitive-text detection
  - Scan prose and metadata for emails, phone numbers, national ID patterns, or other likely PII; report findings as errors (must-redact) or warnings.
  - Output: PII matches with file/location and snippet.
- Reading-level estimation
  - Provide a simple estimate (Flesch‑Kincaid grade) per chapter part/chapter and surface unusually high or low grades as info/warning.
  - Output: numeric grade and guidance.
- Revision & timestamp hygiene
  - Require last_updated and revision_history for mutable objects; flag missing or malformed timestamps.

Report formats (machine-consumable)
- continuity_report.jsonc (per chapter): existing template—used to list contradictions and recommended actions.
- checks_report.jsonc (aggregated): { id, generated_at, issues: [{type, severity, file, location, detail, recommendation}], summary:{errors,warnings,infos} }

Example checks_report.jsonc (summary)
{
  "id": "checks-2025-12-16T20:00:00Z",
  "generated_at": "2025-12-16T20:00:00Z",
  "issues": [
    { "type": "broken_reference", "severity": "error", "file": "story/chapters/chap-02.jsonc", "detail": "pov_character_id 'char-unknown' not defined", "recommendation": "Define character or correct id" }
  ],
  "summary": { "errors": 1, "warnings": 2, "infos": 0 }
}

Automation & CI guidance
- Run step sequence:
  1. schema validation
  2. id / cross-reference checks
  3. word-count & config checks
  4. continuity checks (generate continuity_report.jsonc files)
  5. aggregate to checks_report.jsonc
- CI behavior: fail on any error-level issues; expose warnings in PR checks; attach continuity_report.jsonc and checks_report.jsonc to CI artifacts.
- Suggested tooling: ajv/ajv-cli (JSON schema validation), a small Node/Python script to perform cross-references and continuity rules, or a Copilot prompt that implements the checks and outputs JSON.

Sample Copilot prompts
- "Run schema validation across story/ and templates/ against their schemas; return JSON array of schema errors."
- "Run cross-reference checks for story: list broken references and missing ids, output checks_report.jsonc."
- "Run continuity checks on chapter 'chap-01' and return continuity_report.jsonc with any contradictions, missing references, and recommended fixes."

Update rules & remediation workflow
- For each error-level issue, add an entry to the relevant object's revision_history noting the fix and the CI ticket/PR id.
- For continuity contradictions, prefer human review: automatically suggest fixes but require author approval before applying changes.
- Record automated fixes in a machine note: {date, tool: "auto-checker", action, note} appended to revision_history.

Quick-reference checklist (for reviewers / Copilot)
- All JSONC files validate against schema.
- No duplicate IDs.
- All referenced IDs exist.
- Chapter & part word counts conform to story_config.
- Each chapter/part has a summary and revision_history entry with timestamp.
- Continuity reports show zero error-level contradictions and acceptable warnings.

## Full-check pass (one-command validation)
Purpose
- Run a single comprehensive validation that executes all checks described in "Checks, validation & CI" and produces per-chapter continuity reports plus an aggregated checks_report JSONC.

What it runs (full list)
- Lightweight schema validation (presence of required fields).
- ID uniqueness & format check (short-kebab).
- Cross-reference integrity (characters, locations, parts, plot_line ids).
- Chapter/part sequencing and file existence.
- Word-count checks against story/story_config.jsonc (chapter and part bounds).
- Continuity heuristics (appearance-before-first-appearance, character trait contradictions such as mentions of scars vs character appearance, missing inhabitants, unreferenced objects).
- Sensitive data / redaction checks (secrets marked redacted: true must not appear verbatim in prose).
- External sources & attribution validation (`sources` arrays exist and include name/url/retrieval_date). Validate URLs are well-formed.
- Interaction logs validation (participants exist, referenced locations/chapters exist).
- Plot vs story_config consistency (chapter counts, plot_line counts).
- PII detection (email/phone/id-like patterns) across prose and metadata.
- Reading-level estimation (Flesch‑Kincaid grade estimate).
- Revision & timestamp hygiene (last_updated and revision_history presence).
- Output generation: story/continuity/continuity-chap-<NN>-<timestamp>.jsonc and story/continuity/checks-report-<timestamp>.jsonc.

How to run (local, free-only)
- Invoke locally (no hosted or paid CI required):
  - python tools/run_checks.py --full
- The command will exit with code:
  - 2 if any error-severity issues found,
  - 1 if only warnings found,
  - 0 if no errors/warnings.
- All report files will be written under story/continuity/ and referenced in chapter metadata where applicable.

Example usage prompt for Copilot (free-only)
- "Run the full check pass (python tools/run_checks.py --full). Return the aggregated checks_report and any continuity reports with a short summary."

Notes & policy
- Full passes must be run locally or in self-hosted environments. Do NOT rely on hosted CI or paid services.
- If schema validation or additional checks require a local dependency (e.g., `jsonschema`), the script will detect and print a friendly instruction to install it via pip; no paid or external hosting is required.

End of new section.

## Appendix: templates
See the templates/ folder for:
- Schemas: character_schema.jsonc, location_schema.jsonc, chapter_schema.jsonc, interaction_schema.jsonc, continuity_report.jsonc
- Prompt examples: prompt_templates.md

End of document.

## Copilot-managed checks & responsibilities
- The assistant (Copilot) is designated to run checks locally on demand and is responsible for executing the Full-check pass described above.
- Invocation: user prompt examples:
  - "Run full check now and return checks_report and continuity reports."
  - "Run checks for chap-03 only and summarize high-severity issues."
- Execution rules:
  - Always run locally / self-hosted / free-only tools (python tools/run_checks.py --full).
  - Produce per-chapter continuity_report.jsonc and an aggregated checks-report JSONC under story/continuity/.
  - Update affected chapter metadata with a `checks` object: { last_run, report, continuity_report, status } and append a revision_history entry noting the run and its outcome.
- Remediation policy:
  - For error-level issues, report results and recommended actions; do NOT auto-apply destructive fixes without explicit author approval.
  - For low-risk fixes (typos, metadata formatting) the assistant MAY apply changes automatically if the user has given prior permission; record such automated actions in revision_history with tool metadata.
- Reporting & follow-up:
  - When checks complete, return a concise summary (errors/warnings/info counts), paths to report artifacts, and prioritized recommended fixes.
  - For continuity contradictions, include suggested fixes and require explicit approval before applying substantive changes.
- Privacy & sourcing:
  - Any checks that query external sources must follow the free-only MCP/search policy and include `sources` entries with attribution and retrieval_date.
- Example user prompt:
  - "Copilot, run the full check (python tools/run_checks.py --full), attach the checks_report and continuity reports, and list recommended fixes (do not apply any fixes)."

## Automated iterative rewrite loop

Purpose
- If an assessment reports story_quality below the configured threshold (story_config.assessment_rewrite_threshold), Copilot will propose or perform a targeted rewrite for the affected chapter parts, then re-run the full-check + assessment cycle until the chapter meets the threshold or max iterations is reached.

When to trigger
- After a full-check pass with assessments, for any chapter whose story_quality < assessment_rewrite_threshold.

Behavior & constraints
- Use guidance from story_config.rewrite_guidance and preserve POV, core facts, and metadata.
- Each rewrite iteration should not change chapter meaning; aim to increase tension, tighten prose, and respect word-change limits (story_config.rewrite_word_change_max_percent).
- By default, Copilot will create suggested rewrite artifacts under story/rewrites/chap-<NN>-iter-<MM>.md and not auto-apply them.
- If `auto_apply_rewrites` is true, Copilot will apply the rewrite to part files and chapter prose automatically, but only up to `max_rewrite_iterations` and only when `auto_rewrite_enabled` is true.

Safety & approval
- Destructive or substantive changes always require explicit author approval unless the author has granted prior blanket permission for auto-apply (auto_apply_rewrites = true).
- All rewrites (suggested or applied) are logged in chapter `revision_history` with tool metadata {date, tool: "copilot-rewrite", iteration, note}.
- After each applied rewrite, Copilot runs the full-check and re-assesses. If any error-level issues appear, Copilot stops and reports them for manual review.

Artifacts & reporting
- Suggested rewrites: story/rewrites/chap-<NN>-iter-<MM>.md
- Applied rewrites recorded in revision_history; backup copies saved under story/rewrites/backups/
- Rewrite report included in aggregated checks_report.artifacts.rewrites and adds per-iteration entries.

Example prompts (invoke Copilot)
- "Run full check + assessments and auto-run iterative rewrites up to threshold (use story_config settings). Apply minor fixes only; do not apply large changes without approval."
- "Show suggested rewrites for chapters below threshold; do not apply."

## Simulated runs & artifact generation (official)
- Copilot will simulate full-check passes, iterative rewrites, and assessments in-repo and generate machine-readable artifacts (continuity reports, checks reports, assessments, and rewrite reports) under story/continuity/ and story/rewrites/.
- These simulations are deterministic and designed to support quick iteration without requiring a local "assistant agent" or hosted services.
- If you prefer to run checks locally on your machine, you may run: python tools/run_checks.py --full (this executes the same checks on your machine; no paid services are required).
- Note: previous instructions about running a local assistant agent have been deprecated and removed.

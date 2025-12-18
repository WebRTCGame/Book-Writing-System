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

### Tone & Rhythm integration (new)
- Purpose: Use the tonal model in Tone.md to plan and validate how emotional "waves" and chapter-level rhythms distribute across the book.
- Canonical schema & guidance: `copilot-instructions/templates/tone_schema.jsonc` — defines allowed `macro_phases`, `chapter_level_rhythms`, `scene_rhythms`, `act_level_rhythms`, `character_internal_states`, and `thematic_stages`. Use this file as the authoritative enum source for checks and planners.
- New metadata fields (chapter level): `dominant_tone` (string), `macro_phase` (string from a story-wide `macro_rhythm_sequence`), `chapter_level_rhythm` (one of `Expectation`, `Disruption`, `PartialResolution`). These fields are optional but **strongly recommended** for planning and automated checks.
- Story configuration: `macro_rhythm_sequence` (ordered array of macro phases), `rhythm_cycles` (integer — how many times the macro sequence repeats in the book), `acts_per_book`/`acts` (act-level settings), and `tone_guidelines_file` (path to Tone.md or other guidance).
- Planner & tools:
  - Use `tools/plan_rhythm.py` to compute an overall mapping of chapters → macro phases and to generate `story/tone_plan.jsonc` and `story/act_plan.jsonc`.
  - The planner supports `--annotate-suggestions` (writes a dry-run suggestions file under `story/suggestions/suggested-annotations-<ts>.jsonc`) and `--apply` (applies suggested annotations in-place). This repository is configured to **auto-apply** suggestions by default (`story_config.acts.auto_apply_annotations: true`) — when `--apply` runs it will write an `apply-results-<ts>.jsonc` artifact in `story/suggestions/` and append `revision_history` entries to affected files.
- Planning rules:
  - Use `chapters_per_book` to compute an even distribution of macro phases across the book when `macro_rhythm_sequence` and `rhythm_cycles` are present. Each chapter is mapped to a macro phase by position; the midpoint chapter is expected to contain a tonal inversion (optimism → constraint / loss) — flag it if `macro_phase` is not set or disagrees with expected placement.
  - Each chapter should declare a `chapter_level_rhythm` to help the assistant plan endings that avoid emotional zeros: prefer chapter endings with a question, recontextualization, shift of power, or moral discomfort.
  - Parts may include `scene_rhythm` (e.g., `Tension`, `Action`, `Aftermath`) to guide pacing at the page/scene level; the planner and checks will **suggest** adding `scene_rhythm` to long parts and may auto-apply those suggestions when `auto_apply_annotations` is enabled.
- Checks to add to CI (behavioral):
  - Presence: warn if `dominant_tone` / `macro_phase` / `chapter_level_rhythm` are missing (severity configurable via `story_config` / policies).
  - Distribution: compute expected macro phase per chapter based on `macro_rhythm_sequence`, `rhythm_cycles`, and `chapters_per_book`; warn if a chapter's `macro_phase` conflicts strongly with expected phase (run_checks validates values against `tone_schema.jsonc` and will error on unknown enums).
  - Midpoint inversion check: verify the chapter near the middle of the book shows tonal inversion traits (e.g., shift from lack → consequences); warn if missing.
  - Granularity: recommend adding `scene_rhythm` to parts when parts exceed 6–10 pages or when pacing feels uneven; suggestions are included in planner output and may be applied automatically if allowed.
- How the assistant should use these fields:
  - When generating outlines or chapter suggestions, set or propose `dominant_tone`, `chapter_level_rhythm`, and `macro_phase` entries consistent with the planned rhythm; include short quotes from `tone_guidelines_file` when relevant.
  - When running full checks, include tone/rhythm notes in `continuity_report.jsonc` and the aggregated `checks_report.jsonc`. Severity for tone/act issues is configurable via `story_config` (see Acts policy) and mapped by `tools/act_policy.py`.
- Documentation & human review: use `tone_guidelines_file` (e.g., `Tone.md`) as the canonical guidance for writers; the assistant should quote the relevant line when making a recommendation (short quote + citation path).



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
- Unit tests covering the planner, act policy mapping, and auto-apply flows are available under `tests/` and can be executed with `pytest` to validate behavior and prevent regressions.

## Best practices
- Be explicit about POV, tense, voice, and length in every generation prompt.
- Ask for short, testable outputs (structured JSON + short prose examples).
- Keep single-purpose prompts (create, update, summarize, check).
- Require explicit author approval for any metadata changes beyond minor edits.

## Quick reference & sample prompts
- "Create character using character_schema.jsonc. Provide one-paragraph sample scene separate from the JSON."
- "Update char-xxx: set current_state to 'interrogating captain' and add tag 'on-mission'. Return updated JSON only."
- "Generate chap-03 outline (500–800 words, present tense, Lena POV); return chapter_schema and outline markdown."
- "Plan macro rhythm across the book using Tone.md: given story_config.chapters_per_book and rhythm_cycles, return a table mapping chapter numbers to expected macro_phase and suggested chapter_level_rhythm (Expectation/Disruption/PartialResolution)."
- "Run the planning script (python tools/plan_rhythm.py) to generate `story/tone_plan.jsonc` (and `story/act_plan.jsonc`) and optionally annotate chapters with the suggested `macro_phase` and `chapter_level_rhythm` values; use `--annotate-suggestions` for a dry run and `--apply` to apply changes (artifacts written to `story/suggestions/`)."
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

## Acts & high-level structure

Purpose
- Model the book as a sequence of acts following the Tone.md act-level architecture (default main acts: 7 — Act I..Act VII). An optional **Act 0 – Baseline** may be included via `story_config.baseline_act_included` to capture the opening equilibrium before the intrusion.

Act distribution & percentages
- By default the repository uses a Tone.md aligned distribution (Act 0..Act VII):
  - `act-00`: 5% (Baseline Equilibrium)
  - `act-01`: 10% (Intrusion)
  - `act-02`: 15% (Orientation)
  - `act-03`: 15% (Expansion)
  - `act-04`: 10% (Tonal Inversion / Midpoint)
  - `act-05`: 20% (Constriction)
  - `act-06`: 15% (Collapse)
  - `act-07`: 10% (Resolution)
- You can override this via `story_config.act_distribution` (an ordered mapping of `{"act-id": percent}`). When `act_distribution` is not provided the planner will use the default Tone.md distribution when `acts_per_book` is 7 and `baseline_act_included` is true; otherwise it will evenly split chapters across `acts_per_book`.
- Example `story_config` snippet:

  ```jsonc
  "acts_per_book": 7,
  "baseline_act_included": true,
  "act_distribution": {
    "act-00": 5,
    "act-01": 10,
    "act-02": 15,
    "act-03": 15,
    "act-04": 10,
    "act-05": 20,
    "act-06": 15,
    "act-07": 10
  }
  ```

- The planner (`tools/plan_rhythm.py`) will compute per-act chapter counts using distribution percentages and write `story/act_plan.jsonc` and `story/tone_plan.jsonc`.

Guidance
- Each act should be represented by an `acts/*.jsonc` file following the `copilot-instructions/templates/acts_schema.jsonc` template and include: `id`, `title`, `sequence`, `chapters` (array of chapter ids, contiguous preferred), `dominant_tone`, `macro_phase_segment`, `act_level_rhythm`, `summary`, `estimated_word_count`, `actual_word_count`, and `revision_history`.
- Acts map higher-level macro-rhythm segments to contiguous chapters; e.g., Act I covers early "Hope→Unease" segments, Act II covers "Threat→Loss", and Act III covers "Resolve→Meaning" (customizable via `story_config.act_rhythm_mapping_rules`).
- Canonical act-level rhythm enums (used by checks & planner): `Setup`, `Escalation`, `Crisis`, `Resolution`, `Coda`. Prefer using these enums for `act_level_rhythm`; if you prefer custom labels (e.g., 'Lock-in', 'Pressure'), map them to the canonical set in the act file's `notes` or use `macro_phase_segment` for detailed tone guidance.
- Prefer contiguous chapter ranges per act to simplify automated checks and planning; if non-contiguous acts are required, mark them explicitly and document reasons in the act `notes`.

Checks & automation
- Presence: warn if `acts/*.jsonc` files are missing or if `acts_per_book` in `story_config.jsonc` is set but no act files exist.
- Coverage: ensure every chapter is assigned to exactly one act unless explicitly marked `unassigned:true` (warn if a chapter lacks an act_id or is assigned to multiple acts).
- Contiguity: warn when chapters within an act are non-contiguous.
- Act-level tone: validate `act.macro_phase_segment` against `story_config.macro_rhythm_sequence` and warn when an act's declared segment is inconsistent with expected macro phases for its chapter range.
- Policy-driven severity: the severity for act-related issues (presence, coverage, contiguity, and tone mismatch) is configurable in `story_config.acts.policy` and mapped by `tools/act_policy.py`; CI or local checks will honor those severities when aggregating reports.
- Midpoint & act-boundary checks: verify tonal inversion or escalation is present at act boundaries (e.g., the end of Act I or midpoint of Act II); warn or error depending on policy settings.

How Copilot uses acts
- The planner (`tools/plan_rhythm.py`) computes both a `story/tone_plan.jsonc` (chapter→macro phase map) and a `story/act_plan.jsonc` (summary per act with suggested act-level rhythms and flags such as midpoint, inversion, or boundary concerns).
- Planner modes:
  - `--annotate-suggestions`: write proposed annotations to `story/suggestions/suggested-annotations-<ts>.jsonc` (dry-run, reviewable).
  - `--apply`: apply suggested annotations to chapter JSON files. When `story_config.acts.auto_apply_annotations` is true (the default in this repo), the planner may auto-apply suggestions; it will create an `apply-results-<ts>.jsonc` artifact under `story/suggestions/` and append `revision_history` entries to modified files.
- When generating outlines or rewrites, Copilot should propose `act_id` for new chapters and propose `dominant_tone` and `macro_phase_segment` for acts that match the larger rhythm plan.
- Use `tools/act_policy.py` to determine severity and recommended remediation steps for act-tone mismatches before applying or suggesting fixes.


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
- Tone & rhythm checks
  - Verify presence of tonal metadata (chapter.dominant_tone, chapter.macro_phase, chapter.chapter_level_rhythm) and surface warnings when missing.
  - Validate distribution of macro phases across the book using `story_config.macro_rhythm_sequence` and `story_config.rhythm_cycles`; warn when chapters strongly deviate from planned placement.
  - Check the midpoint chapter for tonal inversion characteristics and warn if missing.
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
  4. tone/rhythm distribution & presence checks (validate chapter.macro_phase, chapter.chapter_level_rhythm; verify midpoint inversion)
  5. continuity checks (generate continuity_report.jsonc files)
  6. aggregate to checks_report.jsonc
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

### New tools & templates (recent additions)
- Canonical tone schema: `copilot-instructions/templates/tone_schema.jsonc` (canonical enums used by checks and planners).
- Acts schema: `copilot-instructions/templates/acts_schema.jsonc` (act metadata template).
- Planner script: `tools/plan_rhythm.py` — generates `story/tone_plan.jsonc` and `story/act_plan.jsonc`, writes suggestion artifacts to `story/suggestions/`, and supports `--annotate-suggestions` and `--apply` modes.
- Act policy helper: `tools/act_policy.py` — maps policy config to severity and recommended actions used by `tools/run_checks.py`.
- Auto-apply & artifacts: `story/suggestions/` contains `suggested-annotations-<ts>.jsonc` (dry-run) and `apply-results-<ts>.jsonc` (applied annotations summary). Planner can create or annotate chapters when `auto_apply_annotations` is enabled.
- Tests: unit tests added under `tests/` that exercise planner annotation output, act policy severity mapping, and auto-apply behavior (`tests/test_act_policy.py`, `tests/test_plan_annotations.py`, `tests/test_auto_apply_annotations.py`).

## Appendix: templates
See the templates/ folder for:
- Schemas: character_schema.jsonc, location_schema.jsonc, chapter_schema.jsonc, interaction_schema.jsonc, continuity_report.jsonc
- Prompt examples: prompt_templates.md

End of document.

## Copilot-managed checks & responsibilities
- The assistant (Copilot) **simulates** checks and produces deterministic, machine-readable artifacts (simulated continuity reports, checks reports, and rewrite suggestions); Copilot does **not** execute repository `.py` scripts on the user's machine by itself.
- Invocation: user prompt examples (simulation):
  - "Simulate a full check and return checks_report and continuity reports."
  - "Simulate checks for chap-03 only and summarize high-severity issues."
- Execution rules (simulation-first):
  - Copilot will **simulate** schema validation, ID/cross-reference checks, tone/rhythm checks, PII detection, and assessment heuristics and present a checks_report-like summary.
  - If the user explicitly requests that the checks be executed locally, Copilot will provide the exact commands to run (e.g., `python tools/run_checks.py --full`) and clear instructions on how to run them and interpret results, but the user runs them locally — Copilot will not run them itself.
  - When simulating a run, Copilot will state which artifacts it would write (e.g., `story/continuity/checks-report-<ts>.jsonc`) and provide a human-readable summary of simulated issues.
  - Copilot will also indicate any file edits it would make (annotations, rewrites) and require explicit confirmation before writing files in-repo.
- Remediation policy:
  - For error-level issues, Copilot will report results and recommended actions; it will not auto-apply destructive fixes without explicit author approval.
  - For low-risk fixes (typos, metadata formatting) the assistant may apply changes automatically only when the user has given prior permission; record such automated actions in `revision_history` with tool metadata.
  - NOTE: tone/act annotation suggestions from `tools/plan_rhythm.py` may be auto-applied in-place when `story_config.acts.auto_apply_annotations` is true (the default in this repository); such actions are recorded with an `apply-results-<ts>.jsonc` artifact and revision_history entries. Substantive rewrites still require explicit author approval unless `auto_rewrite_enabled` is set and within configured limiters.
- Reporting & follow-up:
  - After a simulated run, Copilot returns a concise summary (errors/warnings/info counts), sample artifacts and their paths, and prioritized recommended fixes.
  - For continuity contradictions, Copilot will include suggested fixes and require explicit approval before applying substantive changes.
- Privacy & sourcing:
  - Any checks that query external sources must follow the free-only MCP/search policy and include `sources` entries with attribution and retrieval_date.
- Example user prompts and behaviors:
  - "Simulate the full check and show top issues" → Copilot: provides a simulated checks_report summary and exact local command to run the real script.
  - "Apply planner suggestions and then simulate a check" → Copilot: applies metadata annotations only after confirmation, writes `apply-results` (if editing files), and simulates a follow-up checks_report.

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

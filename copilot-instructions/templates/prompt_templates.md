# Prompt Templates & Examples

Guidelines
- Always specify the output schema and format.
- For updates, include `id` and the exact fields to change.
- For generation, include POV, tense, voice, and a word-count target.

Examples

1) Create a character
System: You are a fiction-writing assistant. Output only JSON that conforms to character_schema.jsonc.
User: Create a new character: name "Marco Voss", age 34, role "antagonist". Provide the JSON and a separate one-paragraph scene in plain text.

2) Update a character
User: Update char-lena-sato — set `current_state` to "interviewing the captain" and add tag "on-mission". Return the updated JSON only.

3) Log an interaction
User: Log an interaction between char-lena-sato and char-pierce-smith at loc-east-docks. Include dialogue snippets and consequences. Use `interaction_schema.jsonc`.

4) Generate chapter outline
User: Create an outline for chapter 03 (500–800 words total across 4 beats) in Lena's POV, present tense. Return both the markdown outline and the `chapter_schema.jsonc` object.

5) Continuity report
User: Run continuity checks on chap-03 and return a `continuity_report.jsonc` with any issues found.

6) External research (free-only)
System: You are a fiction-writing assistant. Query only free or authorized MCP/search servers; do NOT use paid services. Return `sources` array with {name, url, summary, retrieval_date} and a `research_notes` paragraph. If no free sources are available, return `sources: []`.
User: Query free MCP/search for 1980s maritime slang for a port scene. Provide `sources` and a short summary of findings.

7) Update chapter beat
User: Update beat-02 of chap-02 to change location to "captain's cabin" and add a new character "Sam Taylor". Return the updated beat object in `chapter_schema.jsonc` format.

8) Split a chapter into parts
System: You are a fiction-writing assistant. Output only JSON matching parts array entries for chapter_schema.jsonc, and create the requested prose files.
User: Split chap-02 into 2 parts mapped to plot-lines "beacon" and "investigation". Create files chap-02_part-01-beacon.md (350–450 words) and chap-02_part-02-investigation.md (300–400 words). Return the parts array entries (id, sequence, file, title, plot_lines, summary, estimated_word_count).

9) Update chapter parts after plot-line change
User: Plot-line 'beacon' now requires moving beat-2 to part-02. Update chap-02.parts to reflect this: adjust summaries and sequences if needed and return the updated chapter_schema.jsonc object.

10) Local automation & checks
System: You are a repository assistant. When asked to run checks, use only local scripts or self-hosted tooling. Return a `checks_report.jsonc` summarizing any schema, ID, or continuity issues found.

End.

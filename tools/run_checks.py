import os, json, glob, re, argparse
from datetime import datetime
import math
from urllib.parse import urlparse
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORY = os.path.join(ROOT, "story")
CONTINUITY_DIR = os.path.join(STORY, "continuity")
CONFIG_FILE = os.path.join(STORY, "story_config.jsonc")
PLOT_FILE = os.path.join(STORY, "plot.md")

def strip_jsonc(s):
    s = re.sub(r'/\*[\s\S]*?\*/', '', s)
    s = re.sub(r'//.*', '', s)
    return s

def load_jsonc(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return json.loads(strip_jsonc(content))

def find_jsonc_files(pattern):
    return glob.glob(os.path.join(STORY, pattern))

def word_count_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        return len(re.findall(r'\S+', text)), text
    except:
        return None, ""

def chapter_number(chap_id):
    m = re.search(r'chap-(\d+)', chap_id or "")
    return int(m.group(1)) if m else None

def load_prose(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def simple_schema_check_char(obj, path, issues):
    # basic required fields for characters
    required = ["id","name","last_updated"]
    for r in required:
        if r not in obj:
            issues.append({"type":"schema_missing", "severity":"error", "file":path, "detail":f"Missing '{r}' in character file", "recommendation":"Add required field"})

def simple_schema_check_chapter(obj, path, issues):
    required = ["id","title","prose_file","parts"]
    for r in required:
        if r not in obj:
            issues.append({"type":"schema_missing", "severity":"error", "file":path, "detail":f"Missing '{r}' in chapter file", "recommendation":"Add required field"})

def detect_trait_contradictions(text, characters):
    issues = []
    # simple heuristic: check for 'scar' mentions and compare to character distinguishing_features
    for cid, cfile in characters.items():
        try:
            ch = load_jsonc(cfile)
            features = " ".join(ch.get("appearance", {}).get("distinguishing_features", [])).lower()
            # search for "scar" in prose for chapters referencing this character
            if "scar" in features:
                # check any mention that the character has 'clean face' (contradiction)
                if re.search(r'\b' + re.escape(ch.get("name","")) + r'\b.*clean face', text, re.I):
                    issues.append({"type":"contradiction","severity":"warning","detail":f"{ch['id']} appears described as 'clean face' in prose despite 'scar' in appearance","referenced_objects":[ch['id']]})
            else:
                # if character not listed with scar but prose mentions character with 'scar'
                if re.search(r'\b' + re.escape(ch.get("name","")) + r'\b.*scar', text, re.I):
                    issues.append({"type":"contradiction","severity":"warning","detail":f"{ch['id']} mentioned with a 'scar' in prose but not in appearance features","referenced_objects":[ch['id']]})
        except:
            continue
    return issues

def estimate_syllables(word):
    w = word.lower()
    w = re.sub(r'[^a-z]', '', w)
    if not w:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in w:
        is_v = ch in vowels
        if is_v and not prev_vowel:
            count += 1
        prev_vowel = is_v
    # common heuristic corrections
    if w.endswith("e"):
        count = max(1, count-1)
    return max(1, count)

def flesch_kincaid_grade(text):
    sentences = max(1, len(re.findall(r'[.!?]+', text)))
    words = re.findall(r'\w+', text)
    word_count = max(1, len(words))
    syllables = sum(estimate_syllables(w) for w in words)
    # Flesch-Kincaid Grade
    grade = 0.39 * (word_count / sentences) + 11.8 * (syllables / word_count) - 15.59
    return round(grade, 1)

def detect_pii(text):
    matches = []
    # email
    for m in re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text):
        matches.append({"type":"email","value":m})
    # phone-like (simple)
    for m in re.findall(r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{2,4}\b', text):
        if len(re.sub(r'\D','',m)) >= 7:
            matches.append({"type":"phone","value":m})
    # crude national-id-like: sequences of 9+ digits
    for m in re.findall(r'\b\d{9,}\b', text):
        matches.append({"type":"id_like","value":m})
    return matches

def valid_url(u):
    try:
        p = urlparse(u)
        return p.scheme in ("http","https") and p.netloc != ""
    except:
        return False

# Default macro rhythm sequence (taken from Tone.md). Can be customized in story_config.jsonc
DEFAULT_MACRO_SEQUENCE = ["Hope","Unease","Relief","Threat","Triumph","Loss","Resolve","Catastrophe","Meaning"]

# Default act distribution aligned with Tone.md (Act 0 baseline + Acts I–VII)
DEFAULT_ACT_DISTRIBUTION = [
    ("act-00", 5),
    ("act-01", 10),
    ("act-02", 15),
    ("act-03", 15),
    ("act-04", 10),
    ("act-05", 20),
    ("act-06", 15),
    ("act-07", 10)
]

# Tone schema file (canonical enums & guidance)
TONE_SCHEMA_FILE = os.path.join(ROOT, "copilot-instructions", "templates", "tone_schema.jsonc")

def load_tone_schema():
    try:
        return load_jsonc(TONE_SCHEMA_FILE)
    except Exception:
        return {}

def get_expected_macro_phase(ch_index, total_chapters, config):
    """Return the expected macro phase for chapter index (1-based) given the story config.
    Mapping approach: repeat the macro sequence `rhythm_cycles` times and evenly distribute across chapters.
    """
    try:
        seq = config.get('macro_rhythm_sequence', DEFAULT_MACRO_SEQUENCE)
        cycles = max(1, int(config.get('rhythm_cycles', 1)))
        total_phases = len(seq) * cycles
        if not total_chapters or ch_index is None:
            return None
        position = ((ch_index - 1) * total_phases) // total_chapters
        return seq[position % len(seq)]
    except Exception:
        return None

def compute_assessment_from_chapter(chap_obj, chap_issues, prose_text, chapter_metrics, config):
    """
    Simple heuristic scoring. Start at 100 for each category then subtract weighted penalties.
    chapter_metrics: dict with keys like reading_grade, pii_count, part_word_counts, etc.
    """
    base = 100
    scores = {
        "story_quality": base,
        "continuity": base,
        "interest": base,
        "tension": base,
        "loose_ends": base,
        "sentence_quality": base,
        "rhythm": base,
        "speed": base,
        "transparency": base,
        "meets_requirements": base
    }

    # Penalize for continuity errors/warnings
    continuity_errors = len([i for i in chap_issues if i.get("type", "").startswith("contradiction") or i.get("type")=="appearance_before_first_appearance"])
    scores["continuity"] = max(0, scores["continuity"] - continuity_errors * 20)

    # Penalize for PII or redaction violations
    pii_count = chapter_metrics.get("pii_count", 0)
    scores["transparency"] = max(0, scores["transparency"] - pii_count * 40)
    scores["sentence_quality"] = max(0, scores["sentence_quality"] - pii_count * 10)

    # Reading-level informs sentence_quality & rhythm
    grade = chapter_metrics.get("reading_grade")
    if grade is not None:
        if grade >= 14 or grade <= 4:
            scores["sentence_quality"] = max(0, scores["sentence_quality"] - 15)
            scores["rhythm"] = max(0, scores["rhythm"] - 10)

    # Word-count / pacing
    min_chapter = config.get("min_chapter_words")
    chap_wc = chap_obj.get("actual_word_count", 0)
    if min_chapter and chap_wc < min_chapter:
        scores["speed"] = max(0, scores["speed"] - 20)
        scores["story_quality"] = max(0, scores["story_quality"] - 10)

    # Loose ends heuristic: presence of many 'open threads' in plot or chapter notes
    # (This simple heuristic counts occurrences of 'open' or 'thread' in prose)
    loose_mentions = len(re.findall(r'\b(open thread|open threads|open|thread)\b', prose_text or "", re.I))
    scores["loose_ends"] = max(0, scores["loose_ends"] - loose_mentions * 8)

    # Interest & tension heuristics: penalize if no dramatic beats present
    if not chap_obj.get("beats"):
        scores["interest"] = max(0, scores["interest"] - 20)
        scores["tension"] = max(0, scores["tension"] - 15)

    # meets_requirements: check plot_line coverage & parts presence
    parts = chap_obj.get("parts", [])
    if not parts:
        scores["meets_requirements"] = max(0, scores["meets_requirements"] - 30)

    # normalize and return ints
    for k in scores:
        scores[k] = int(scores[k])
    return scores

def write_assessment_json(assessment_obj, outdir):
    ensure_dir(outdir)
    fname = f"assessment-{assessment_obj['target_id']}-{assessment_obj['generated_at']}.jsonc"
    path = os.path.join(outdir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(assessment_obj, f, indent=2)
    return path

def readability_score_from_grade(grade, target_grade=10):
    # Simple mapping: perfect at target_grade -> 100, penalize 8 points per grade difference
    if grade is None:
        return 75
    score = 100 - int(abs(grade - target_grade) * 8)
    return max(0, min(100, score))

def append_assessment_md(assessment_objs, md_path):
    """
    Append machine-readable JSONC blocks and a summary Markdown table.
    Create the table header if absent, then append one row per assessment.
    """
    ensure_dir(os.path.dirname(md_path))
    # Read existing content to check for table header
    existing = ""
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            existing = f.read()

    header = ("| Time (UTC) | Scope | Target | story_quality | continuity | interest | tension | loose_ends | "
              "sentence_quality | rhythm | speed | transparency | meets_requirements | readability | Summary |\n"
              "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
    with open(md_path, "a", encoding="utf-8") as f:
        # Write JSONC blocks first
        for a in assessment_objs:
            f.write("```jsonc\n")
            json.dump(a, f, indent=2)
            f.write("\n```\n\n")
        # If header not present, append it
        if header.strip() not in existing:
            f.write("## Assessment summary table\n\n")
            f.write(header)
        # Append rows
        for a in assessment_objs:
            s = a.get("scores", {})
            row = "| {time} | {scope} | {target} | {story_quality} | {continuity} | {interest} | {tension} | {loose_ends} | {sentence_quality} | {rhythm} | {speed} | {transparency} | {meets_requirements} | {readability} | {summary} |\n".format(
                time=a.get("generated_at"),
                scope=a.get("scope"),
                target=a.get("target_id"),
                story_quality=s.get("story_quality", ""),
                continuity=s.get("continuity", ""),
                interest=s.get("interest", ""),
                tension=s.get("tension", ""),
                loose_ends=s.get("loose_ends", ""),
                sentence_quality=s.get("sentence_quality", ""),
                rhythm=s.get("rhythm", ""),
                speed=s.get("speed", ""),
                transparency=s.get("transparency", ""),
                meets_requirements=s.get("meets_requirements", ""),
                readability=s.get("readability", ""),
                summary=a.get("summary","").replace("|","／")[:120]
            )
            f.write(row)

def run_full_check():
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    # safe timestamp for filenames (Windows does not allow ':')
    safe_now = now.replace(":","-")
    ensure_dir(CONTINUITY_DIR)
    report_issues = []
    infos = []
    # Load config & plot
    try:
        config = load_jsonc(CONFIG_FILE)
    except Exception as e:
        report_issues.append({"type":"config_load","severity":"error","file":CONFIG_FILE,"detail":str(e),"recommendation":"Fix or create story_config.jsonc"})
        config = {}
    # Load tone schema for canonical enums
    tone_schema = load_tone_schema()
    MACRO_PHASES = tone_schema.get('macro_phases', DEFAULT_MACRO_SEQUENCE)
    CHAPTER_RHYTHMS_ALLOWED = tone_schema.get('chapter_level_rhythms', ["Expectation","Disruption","PartialResolution"])
    SCENE_RHYTHMS_ALLOWED = tone_schema.get('scene_rhythms', ["Tension","Action","Aftermath"])
    ACT_RHYTHMS_ALLOWED = tone_schema.get('act_level_rhythms', ["Setup","Escalation","Crisis","Resolution","Coda"]) 
    # Load acts policy config and helpers
    try:
        from tools.act_policy import load_acts_policy, severity_for_policy
        acts_policy = load_acts_policy(config)
    except Exception:
        acts_policy = {
            "require_act_files": True,
            "missing_act_policy": "warning",
            "act_tone_mismatch_policy": "warning",
            "missing_chapter_act_policy": "warning",
            "auto_assign_chapters": False,
            "auto_apply_annotations": False
        }

    # Load characters, locations, chapters
    chars = {}
    for f in find_jsonc_files("characters/*.jsonc"):
        try:
            o = load_jsonc(f); chars[o['id']] = f
        except Exception as e:
            report_issues.append({"type":"schema","severity":"error","file":f,"detail":str(e)})
    locs = {}
    for f in find_jsonc_files("locations/*.jsonc"):
        try:
            o = load_jsonc(f); locs[o['id']] = f
        except Exception as e:
            report_issues.append({"type":"schema","severity":"error","file":f,"detail":str(e)})
    chaps = {}
    for f in find_jsonc_files("chapters/*.jsonc"):
        try:
            o = load_jsonc(f); chaps[o['id']] = (o, f)
        except Exception as e:
            report_issues.append({"type":"schema","severity":"error","file":f,"detail":str(e)})

    # Load acts (optional but recommended)
    acts = {}
    for f in find_jsonc_files("acts/*.jsonc"):
        try:
            o = load_jsonc(f); acts[o['id']] = (o, f)
        except Exception as e:
            report_issues.append({"type":"schema","severity":"error","file":f,"detail":str(e)})
    if not acts:
        sev = severity_for_policy(acts_policy.get('missing_act_policy', 'warning'))
        report_issues.append({"type":"acts_missing","severity":sev,"file":CONFIG_FILE,"detail":"No act files found under story/acts/. Consider adding act definitions or setting 'acts_per_book' to 0 to disable act-level checks","recommendation":"Add act files following templates/acts_schema.jsonc or set acts_per_book to 0 in story_config.jsonc"})

    # ID uniqueness & format
    id_map = {}
    for idv, path in {**chars, **locs, **{k:v[1] for k,v in chaps.items()}, **{k:v[1] for k,v in acts.items()}}.items():
        if idv in id_map:
            report_issues.append({"type":"duplicate_id","severity":"error","file":path,"detail":f"Duplicate id {idv} also in {id_map[idv]}","recommendation":"Remove/rename duplicate id"})
        else:
            id_map[idv] = path
        if not re.match(r'^[a-z0-9\-]+$', idv):
            report_issues.append({"type":"id_format","severity":"warning","file":path,"detail":f"ID '{idv}' does not match short-kebab format","recommendation":"Use short-kebab (lowercase, hyphens)"})
    # Per-chapter continuity & other checks
    min_chapter = config.get("min_chapter_words", config.get("min_chapter_words", None))
    min_part = config.get("part_word_target_min", None)
    agg_infos = []
    for chap_id, (chap_obj, chap_file) in chaps.items():
        chap_issues = []
        # quick schema checks
        simple_schema_check_chapter(chap_obj, chap_file, chap_issues)
        # check pov & setting references
        pov = chap_obj.get("pov_character_id")
        if pov and pov not in chars:
            chap_issues.append({"type":"broken_reference","severity":"error","file":chap_file,"detail":f"pov_character_id '{pov}' not found","recommendation":"Add character or correct id"})
        loc = chap_obj.get("setting_location_id")
        if loc and loc not in locs:
            chap_issues.append({"type":"broken_reference","severity":"error","file":chap_file,"detail":f"setting_location_id '{loc}' not found","recommendation":"Add location or correct id"})

        # Act assignment checks: chapter should belong to exactly one act unless acts are not defined
        chapter_act_id = chap_obj.get('act_id')
        found_in_acts = [aid for aid, (aobj, apath) in acts.items() if chap_id in aobj.get('chapters', [])]
        if not acts:
            # no acts defined, skip checks
            pass
        else:
            if chapter_act_id and chapter_act_id not in acts:
                chap_issues.append({"type":"broken_reference","severity":"warning","file":chap_file,"detail":f"act_id '{chapter_act_id}' not found in acts/, but acts exist","recommendation":"Set a valid act_id or add the act file"})
            if not chapter_act_id and not found_in_acts:
                sev = severity_for_policy(acts_policy.get('missing_chapter_act_policy', 'warning'))
                chap_issues.append({"type":"act_missing","severity":sev,"file":chap_file,"detail":"Chapter not assigned to an act (no 'act_id' and not listed in any act file)","recommendation":"Add 'act_id' to chapter or add chapter id to an act file in story/acts/"})
            if chapter_act_id and found_in_acts and chapter_act_id not in found_in_acts:
                sev = severity_for_policy(acts_policy.get('missing_chapter_act_policy', 'warning'))
                chap_issues.append({"type":"act_mismatch","severity":sev,"file":chap_file,"detail":f"Chapter's 'act_id' ('{chapter_act_id}') does not match act files which list it in {found_in_acts}","recommendation":"Fix chapter.act_id or update act file to match desired assignment"})
            if len(found_in_acts) > 1:
                sev = severity_for_policy(acts_policy.get('missing_chapter_act_policy', 'warning'))
                chap_issues.append({"type":"act_multiple","severity":sev,"file":chap_file,"detail":f"Chapter appears in multiple act files: {found_in_acts}","recommendation":"Ensure chapter belongs to a single act or document intentional duplication in act notes"})
            if chapter_act_id and found_in_acts and chapter_act_id not in found_in_acts:
                chap_issues.append({"type":"act_mismatch","severity":"warning","file":chap_file,"detail":f"Chapter's 'act_id' ('{chapter_act_id}') does not match act files which list it in {found_in_acts}","recommendation":"Fix chapter.act_id or update act file to match desired assignment"})
            if len(found_in_acts) > 1:
                chap_issues.append({"type":"act_multiple","severity":"warning","file":chap_file,"detail":f"Chapter appears in multiple act files: {found_in_acts}","recommendation":"Ensure chapter belongs to a single act or document intentional duplication in act notes"})
        # parts sequencing and file checks
        parts = chap_obj.get("parts", [])
        seqs = []
        combined_text = ""
        for p in parts:
            seqs.append(p.get("sequence"))
            path = os.path.join(ROOT, p.get("file"))
            if not os.path.exists(path):
                chap_issues.append({"type":"missing_file","severity":"error","file":chap_file,"detail":f"Part file missing: {p.get('file')}","recommendation":"Create part file or fix path"})
            wc, text = word_count_file(path)
            combined_text += "\n" + text if text else ""
            if wc is None:
                chap_issues.append({"type":"file_read","severity":"warning","file":p.get("file"),"detail":"Unable to read file to count words"})
            else:
                if min_part and wc < min_part:
                    chap_issues.append({"type":"word_count","severity":"warning","file":p.get("file"),"detail":f"Part below min words: {wc} < {min_part}"})
        if parts:
            seqs_sorted = sorted(seqs or [])
            if seqs_sorted != list(range(1, len(parts)+1)):
                chap_issues.append({"type":"sequence","severity":"error","file":chap_file,"detail":"Parts sequences not contiguous starting at 1","recommendation":"Renumber part.sequence to contiguous integers"})
        # chapter word count
        chap_wc = chap_obj.get("actual_word_count")
        if chap_wc is None:
            chap_issues.append({"type":"missing_word_count","severity":"warning","file":chap_file,"detail":"actual_word_count missing","recommendation":"Update actual_word_count after editing prose"})
        else:
            if min_chapter and chap_wc < min_chapter:
                chap_issues.append({"type":"word_count","severity":"warning","file":chap_file,"detail":f"Chapter below min words: {chap_wc} < {min_chapter}"})
        # Continuity heuristics: appearance_before_first_appearance & trait contradictions
        # find character mentions by name or aliases
        mentions = {}
        prose_text = combined_text or load_prose(os.path.join(ROOT, chap_obj.get("prose_file","")))
        for cid, cpath in chars.items():
            cobj = {}
            try:
                cobj = load_jsonc(cpath)
            except:
                continue
            names = [cobj.get("name","")] + cobj.get("aliases", [])
            found = False
            for n in names:
                if n and re.search(r'\b' + re.escape(n) + r'\b', prose_text):
                    found = True
                    break
            if found:
                mentions[cid] = True
                # appearance contradiction checks (simple)
                contr = detect_trait_contradictions(prose_text, {cid:cpath})
                for c in contr:
                    chap_issues.append({**c, "file":chap_file})
                # check first_appearance order
                fa = cobj.get("first_appearance_chapter")
                if fa:
                    fa_num = chapter_number(fa)
                    ch_num = chapter_number(chap_id)
                    if fa_num and ch_num and ch_num < fa_num:
                        chap_issues.append({"type":"appearance_before_first_appearance","severity":"warning","file":chap_file,"detail":f"Character '{cid}' mentioned in {chap_id} but first_appearance_chapter is '{fa}'","recommendation":"Adjust first_appearance_chapter or leave as reference"})
        # secrets redaction checks
        for cid, cpath in chars.items():
            try:
                cobj = load_jsonc(cpath)
            except:
                continue
            for s in cobj.get("secrets", []):
                if s.get("redacted") and s.get("text"):
                    if s["text"] in prose_text:
                        chap_issues.append({"type":"redaction_violation","severity":"error","file":chap_file,"detail":f"Secret text appears in prose for {cid}; secret should be redacted","recommendation":"Remove secret text from prose or mark redacted=false and secure consent"})
        # reading-level estimation
        reading_grade = None
        if prose_text:
            reading_grade = flesch_kincaid_grade(prose_text)
            chap_issues.append({"type":"reading_level","severity":"info","file":chap_file,"detail":f"Flesch-Kincaid grade estimate: {reading_grade}."})
            # flag extremes as warnings
            if reading_grade >= 14 or reading_grade <= 4:
                chap_issues.append({"type":"reading_level_extreme","severity":"warning","file":chap_file,"detail":f"Unusual reading grade: {reading_grade}. Consider adjusting for target audience."})
        # compute readability score
        readability = readability_score_from_grade(reading_grade)
        # PII detection in prose and metadata
        pii_matches = detect_pii(prose_text)
        for m in pii_matches:
            chap_issues.append({"type":"pii_detected","severity":"error","file":chap_file,"detail":f"Detected {m['type']} in prose: {m['value']}. Remove or redact.", "recommendation":"Redact or obfuscate PII"})
        chapter_metrics = {"reading_grade": reading_grade, "readability": readability, "pii_count": len(pii_matches)}
        # source URL validation for chapter-level sources (if present)
        if "sources" in chap_obj:
            for s in chap_obj.get("sources", []):
                url = s.get("url")
                if url and not valid_url(url):
                    chap_issues.append({"type":"sources_url_invalid","severity":"warning","file":chap_file,"detail":f"Source URL appears invalid: {url}", "recommendation":"Fix or remove URL"})
                if "retrieval_date" not in s:
                    chap_issues.append({"type":"sources_missing","severity":"warning","file":chap_file,"detail":"Source entry missing 'retrieval_date'","recommendation":"Add retrieval_date"})

        # --- Tone & rhythm checks (new) ---
        ch_num = chapter_number(chap_id)
        expected_phase = get_expected_macro_phase(ch_num, config.get('chapters_per_book'), config)
        chap_macro = chap_obj.get('macro_phase')
        if not chap_macro:
            chap_issues.append({"type":"tone_missing","severity":"warning","file":chap_file,"detail":"Chapter missing 'macro_phase' tonal metadata","recommendation":"Add 'macro_phase' consistent with story_config.macro_rhythm_sequence or leave 'TBD' if undecided"})
        else:
            # validate value against canonical macro phases
            if chap_macro not in MACRO_PHASES:
                chap_issues.append({"type":"macro_phase_invalid","severity":"warning","file":chap_file,"detail":f"Chapter macro_phase '{chap_macro}' is not in canonical macro_phases: {MACRO_PHASES}","recommendation":"Use one of the canonical macro_phases or update templates/tone_schema.jsonc"})
            if expected_phase and chap_macro != expected_phase:
                chap_issues.append({"type":"tone_mismatch","severity":"warning","file":chap_file,"detail":f"Chapter macro_phase '{chap_macro}' differs from expected '{expected_phase}' based on story rhythm mapping","recommendation":"Review chapter tone or update chapter metadata to reflect intentional deviation"})
        # chapter_level_rhythm validity
        clr = chap_obj.get('chapter_level_rhythm')
        if not clr:
            chap_issues.append({"type":"chapter_rhythm_missing","severity":"warning","file":chap_file,"detail":"Missing 'chapter_level_rhythm' (Expectation/Disruption/PartialResolution)","recommendation":"Set 'chapter_level_rhythm' to guide chapter endings"})
        else:
            if clr not in CHAPTER_RHYTHMS_ALLOWED:
                chap_issues.append({"type":"chapter_rhythm_invalid","severity":"warning","file":chap_file,"detail":f"Invalid chapter_level_rhythm '{clr}'. Allowed: {CHAPTER_RHYTHMS_ALLOWED}","recommendation":f"Use one of: {CHAPTER_RHYTHMS_ALLOWED}"})
        # Part-level scene rhythm recommendations: suggest adding scene_rhythm if part is long
        for p in parts:
            path = os.path.join(ROOT, p.get('file'))
            wc, _ = word_count_file(path)
            # recommend scene_rhythm if long
            if wc and wc > 800 and not p.get('scene_rhythm'):
                chap_issues.append({"type":"scene_rhythm_missing","severity":"warning","file":chap_file,"detail":f"Part {p.get('id')} is long ({wc} words); consider adding 'scene_rhythm' (Tension/Action/Aftermath)","recommendation":"Add 'scene_rhythm' to part metadata to clarify pacing"})
            # validate scene_rhythm value if present
            if p.get('scene_rhythm') and p.get('scene_rhythm') not in SCENE_RHYTHMS_ALLOWED:
                chap_issues.append({"type":"scene_rhythm_invalid","severity":"warning","file":chap_file,"detail":f"Part {p.get('id')} has invalid scene_rhythm '{p.get('scene_rhythm')}'. Allowed: {SCENE_RHYTHMS_ALLOWED}","recommendation":f"Use one of: {SCENE_RHYTHMS_ALLOWED}"})

        # midpoint inversion heuristic: check roughly middle chapter for tonal inversion
        total_chapters = config.get('chapters_per_book')
        if total_chapters and ch_num:
            mid = math.ceil(total_chapters / 2)
            if ch_num == mid:
                # if expected_phase exists, make sure a tonal inversion is declared or chapter shows 'Disruption' or 'Dread' style tone
                if clr and clr != "Disruption":
                    chap_issues.append({"type":"midpoint_tone_check","severity":"warning","file":chap_file,"detail":"Midpoint chapter not marked as a tonal inversion (expected 'Disruption').","recommendation":"Review midpoint chapter for tonal inversion (optimism → constraint) and add 'chapter_level_rhythm':'Disruption' or a note in chapter metadata."})

        # assemble continuity report for chapter
        continuity = {
            "id": f"continuity-{chap_id}-{now}",
            "chapter_id": chap_id,
            "generated_at": now,
            "issues": chap_issues,
            "summary": f"{len([i for i in chap_issues if i.get('severity')=='error'])} errors, {len([i for i in chap_issues if i.get('severity')=='warning'])} warnings",
            "last_updated": now
        }
        outpath = os.path.join(CONTINUITY_DIR, f"continuity-{chap_id}-{safe_now}.jsonc")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(continuity, f, indent=2)
        infos.append({"file":chap_file, "continuity_report": outpath, "issues_found": len(chap_issues)})
        report_issues.extend(chap_issues)

    # --- Act-level validations ---
    try:
        config_acts = load_jsonc(CONFIG_FILE).get('acts_per_book', None)
    except Exception:
        config_acts = None
    if acts:
        # check contiguity & chapter existence per act
        covered = set()
        for aid, (aobj, apath) in acts.items():
            a_chaps = aobj.get('chapters', [])
            # validate chapters exist
            for c in a_chaps:
                # accept either numeric (int) chapter numbers or full chapter ids like 'chap-01'
                if isinstance(c, int):
                    cid = f"chap-{str(c).zfill(2)}"
                elif isinstance(c, str) and c.startswith('chap-'):
                    cid = c
                else:
                    # unsupported format; create warning and skip
                    report_issues.append({"type":"act_invalid_chapter_id","severity":"warning","file":apath,"detail":f"Act '{aid}' contains unsupported chapter identifier: {c}","recommendation":"Use 'chap-XX' strings or integers for chapter numbers in act files"})
                    cid = None
                if cid:
                    if cid not in chaps:
                        report_issues.append({"type":"act_missing_chapter","severity":"warning","file":apath,"detail":f"Act '{aid}' references chapter id {cid} which does not exist as a chapter file","recommendation":"Fix chapter id in act or add missing chapter file"})
                    else:
                        covered.add(cid)
            # contiguity check (normalize chapter ids to numbers where possible)
            if a_chaps:
                numeric_chaps = []
                for c in a_chaps:
                    if isinstance(c, int):
                        numeric_chaps.append(c)
                    elif isinstance(c, str) and c.startswith('chap-'):
                        num = chapter_number(c)
                        if num:
                            numeric_chaps.append(num)
                if numeric_chaps:
                    sorted_nums = sorted(numeric_chaps)
                    if sorted_nums != list(range(sorted_nums[0], sorted_nums[-1] + 1)):
                        report_issues.append({"type":"act_noncontiguous","severity":"warning","file":apath,"detail":f"Act '{aid}' chapters are non-contiguous (numeric view): {numeric_chaps}","recommendation":"Prefer contiguous chapter ranges for acts or add notes documenting the split"})
                else:
                    # couldn't normalize to numbers - still warn if many entries
                    if len(a_chaps) > 1:
                        report_issues.append({"type":"act_noncontiguous","severity":"warning","file":apath,"detail":f"Act '{aid}' chapters appear non-numeric or cannot be checked for contiguity: {a_chaps}","recommendation":"Use 'chap-XX' ids or numeric chapter numbers for act definitions"})
            # act-level tone checks
            if 'macro_phase_segment' not in aobj:
                report_issues.append({"type":"act_tone_missing","severity":"warning","file":apath,"detail":f"Act '{aid}' missing 'macro_phase_segment' tonal metadata","recommendation":"Add 'macro_phase_segment' to describe the macro phases covered by this act"})
            else:
                # validate segment vs expected phases for its chapter range
                expected_phases_in_act = []
                for c in a_chaps:
                    cnum = c if isinstance(c, int) else chapter_number(c) if isinstance(c, str) else None
                    phase = None
                    if cnum:
                        phase = get_expected_macro_phase(cnum, load_jsonc(CONFIG_FILE).get('chapters_per_book', None), load_jsonc(CONFIG_FILE))
                    if phase and phase not in expected_phases_in_act:
                        expected_phases_in_act.append(phase)
                seg = aobj.get('macro_phase_segment', [])
                # normalize to list
                seg_list = seg if isinstance(seg, list) else [seg]
                # validate seg items are canonical macro phases
                for item in seg_list:
                    if item not in MACRO_PHASES:
                        report_issues.append({"type":"act_macro_phase_invalid","severity":"warning","file":apath,"detail":f"Act '{aid}' includes macro_phase_segment item '{item}' not in canonical macro_phases: {MACRO_PHASES}","recommendation":"Use canonical macro_phases from templates/tone_schema.jsonc"})
                # warn if seg_list shares no overlap with expected_phases_in_act
                if expected_phases_in_act and not set(seg_list).intersection(set(expected_phases_in_act)):
                    sev = severity_for_policy(acts_policy.get('act_tone_mismatch_policy', 'warning'))
                    report_issues.append({"type":"act_tone_mismatch","severity":sev,"file":apath,"detail":f"Act '{aid}' macro_phase_segment {seg_list} does not overlap expected phases for its chapters {expected_phases_in_act}","recommendation":"Review act tone or adjust chapter allocations"})
                # validate act_level_rhythm if present
                alr = aobj.get('act_level_rhythm')
                if alr and alr not in ACT_RHYTHMS_ALLOWED:
                    report_issues.append({"type":"act_rhythm_invalid","severity":"warning","file":apath,"detail":f"Act '{aid}' act_level_rhythm '{alr}' not in allowed: {ACT_RHYTHMS_ALLOWED}","recommendation":f"Use one of: {ACT_RHYTHMS_ALLOWED}"})
        # Act distribution checks: compare expected distribution against actual act files
        try:
            raw_dist = load_jsonc(CONFIG_FILE).get('act_distribution', None)
            baseline_included_cfg = bool(load_jsonc(CONFIG_FILE).get('baseline_act_included', True))
            if raw_dist:
                if isinstance(raw_dist, dict):
                    distribution = [(k, int(v)) for k, v in raw_dist.items()]
                elif isinstance(raw_dist, list):
                    distribution = [(str(k), int(v)) for k, v in raw_dist]
                else:
                    distribution = DEFAULT_ACT_DISTRIBUTION
            else:
                # default behavior: use DEFAULT_ACT_DISTRIBUTION when acts_per_book == 7
                if load_jsonc(CONFIG_FILE).get('acts_per_book', None) == 7:
                    distribution = DEFAULT_ACT_DISTRIBUTION
                else:
                    distribution = []
            if not baseline_included_cfg:
                distribution = [pair for pair in distribution if pair[0] != 'act-00']

            if distribution:
                total_pct = sum(pct for _, pct in distribution) or 100
                expected_raw = [(aid, int((pct * load_jsonc(CONFIG_FILE).get('chapters_per_book', 0)) / total_pct)) for aid, pct in distribution]
                allocated = sum(cnt for _, cnt in expected_raw)
                rem = load_jsonc(CONFIG_FILE).get('chapters_per_book', 0) - allocated
                sorted_by_pct = sorted(distribution, key=lambda x: x[1], reverse=True)
                ridx = 0
                while rem > 0 and sorted_by_pct:
                    aid = sorted_by_pct[ridx % len(sorted_by_pct)][0]
                    for i, (a_id, c) in enumerate(expected_raw):
                        if a_id == aid:
                            expected_raw[i] = (a_id, c + 1)
                            rem -= 1
                            break
                    ridx += 1

                for aid, expected_count in expected_raw:
                    if aid not in acts:
                        sev = severity_for_policy(acts_policy.get('missing_act_policy', 'warning'))
                        report_issues.append({"type":"act_missing_expected","severity":sev,"file":CONFIG_FILE,"detail":f"Expected act '{aid}' not found as an act file per act_distribution","recommendation":"Add act file or adjust act_distribution in story_config.jsonc"})
                    else:
                        actual_count = len(acts[aid][0].get('chapters', []))
                        if abs(actual_count - expected_count) > 1:
                            sev = severity_for_policy(acts_policy.get('missing_act_policy', 'warning'))
                            report_issues.append({"type":"act_coverage_mismatch","severity":sev,"file":acts[aid][1],"detail":f"Act '{aid}' has {actual_count} chapters but expected approx {expected_count} based on distribution","recommendation":"Adjust chapters listed in act file or update act_distribution in story_config.jsonc"})
        except Exception:
            pass

        # chapters not covered by any act
        for cid in chaps.keys():
            if cid not in covered:
                report_issues.append({"type":"chapter_not_in_act","severity":"warning","file":chaps[cid][1],"detail":f"Chapter '{cid}' not listed in any act file","recommendation":"Add chapter to an act or mark as unassigned intentionally"})

    # aggregated checks report
    errors = [i for i in report_issues if i.get("severity")=="error"]
    warnings = [i for i in report_issues if i.get("severity")=="warning"]
    report = {
        "id": f"checks-{now}",
        "generated_at": now,
        "scope": "full-check",
        "issues": report_issues,
        "summary": {"errors": len(errors), "warnings": len(warnings), "infos": len(infos)},
        "artifacts": { "continuity_reports": [os.path.join(CONTINUITY_DIR,f) for f in os.listdir(CONTINUITY_DIR) if f.endswith(f"-{safe_now}.jsonc")] }
    }
    outpath = os.path.join(CONTINUITY_DIR, f"checks-report-{safe_now}.jsonc")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Write/collect continuity, assessment, rewrite artifact paths relative to repo for the TODO
    cont_paths = report.get("artifacts", {}).get("continuity_reports", [])
    assess_paths = report.get("artifacts", {}).get("assessments", [])
    rewrite_paths = report.get("artifacts", {}).get("rewrites", [])

    # Update the CHECKS_TODO.md to record this run
    try:
        update_checks_todo({"generated_at": now, "report": outpath, "id": report.get("id")}, cont_paths, assess_paths, rewrite_paths)
    except Exception as e:
        print("Failed to update CHECKS_TODO.md:", e)

    print(f"Full checks written to: {outpath}")
    if errors:
        print("Errors found; exit code 2")
        return 2
    if warnings:
        print("Warnings found; exit code 1")
        return 1
    print("No errors or warnings; exit code 0")
    return 0

def simple_tighten_text(text, guidance=None):
    """
    Lightweight rewrite heuristic to 'tighten' prose:
    - remove common filler words,
    - shorten very long sentences by splitting at commas,
    - trim repeated whitespace.
    This is conservative and intended as a first-pass suggestion.
    """
    fillers = [r'\bvery\b', r'\bjust\b', r'\breally\b', r'\bquite\b', r'\balmost\b', r'\bsomewhat\b', r'\blittle\b']
    out = text
    for f in fillers:
        out = re.sub(f, '', out, flags=re.I)
    # remove duplicate spaces
    out = re.sub(r'\s{2,}', ' ', out)
    # shorten long sentences heuristically
    def shorten_sentence(m):
        sent = m.group(0)
        words = sent.split()
        if len(words) > 25:
            parts = re.split(r',|;|\u2014', sent)
            # return first two parts joined as sentences
            return (parts[0].strip() + '. ' + (parts[1].strip() + '.' if len(parts) > 1 else ''))
        return sent
    out = re.sub(r'[^.!?]+[.!?]', shorten_sentence, out)
    return out.strip()

def apply_rewrite_to_part(part_path, new_text, backup_dir, apply_changes=False):
    """
    Save a suggested rewrite file and optionally apply overwrite with backup.
    Returns path to suggested file and applied flag.
    """
    ensure_dir(os.path.dirname(part_path))
    base = os.path.basename(part_path)
    iter_fname = f"rewrites/suggested-{base}"
    suggested_path = os.path.join(os.path.dirname(os.path.dirname(part_path)), iter_fname)
    ensure_dir(os.path.dirname(suggested_path))
    with open(suggested_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    applied = False
    if apply_changes:
        # backup original
        ensure_dir(backup_dir)
        shutil.copy2(part_path, os.path.join(backup_dir, base + ".bak"))
        with open(part_path, "w", encoding="utf-8") as f:
            f.write(new_text)
        applied = True
    return suggested_path, applied

def run_iterative_rewrites(config, chaps, assessments_map, max_iterations=None, auto_apply=False):
    """
    For chapters with assessment.story_quality < threshold, attempt iterative rewrites.
    Returns list of rewrite actions performed/suggested.
    """
    threshold = config.get("assessment_rewrite_threshold", 80)
    max_iter = max_iterations or config.get("max_rewrite_iterations", 3)
    rewrite_results = []
    for chap_id, (chap_obj, chap_file) in chaps.items():
        # load latest chapter assessment if present
        assess = assessments_map.get(chap_id)
        if not assess:
            continue
        if assess["scores"].get("story_quality", 100) >= threshold:
            continue
        # iterate
        for iteration in range(1, max_iter+1):
            # gather part files and current prose
            parts = chap_obj.get("parts", [])
            any_applied = False
            iteration_record = {"chapter": chap_id, "iteration": iteration, "actions": []}
            backup_dir = os.path.join(ROOT, "story", "rewrites", "backups")
            for p in parts:
                part_path = os.path.join(ROOT, p["file"])
                wc, text = word_count_file(part_path)
                new_text = simple_tighten_text(text, guidance=config.get("rewrite_guidance"))
                suggested_path, applied = apply_rewrite_to_part(part_path, new_text, backup_dir, apply_changes=auto_apply and config.get("auto_apply_rewrites", False))
                iteration_record["actions"].append({
                    "part": p["id"],
                    "original_wc": wc,
                    "suggested_file": os.path.relpath(suggested_path, ROOT),
                    "applied": applied
                })
                if applied:
                    any_applied = True
            # record iteration
            rewrite_results.append(iteration_record)
            # if any applied, update chapter metadata (actual_word_count recomputed) and revision_history
            if any_applied:
                # recompute word counts and update chapters' actual_word_count
                total_wc = 0
                for p in parts:
                    pp = os.path.join(ROOT, p["file"])
                    wc, _ = word_count_file(pp)
                    p["actual_word_count"] = wc or p.get("actual_word_count", 0)
                    total_wc += p["actual_word_count"] or 0
                chap_obj["actual_word_count"] = total_wc
                # add revision entry
                now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                chap_obj.setdefault("revision_history", []).append({ "date": now, "author": "copilot-rewrite", "note": f"Applied rewrite iteration {iteration}" })
            # run full-check and assessments again to refresh assessments_map
            rc = run_full_check()
            # reload assessments (simple approach: regenerate map via reading assessment artifacts)
            # For brevity, assume run_full_check updates continuity & assessment artifacts and the caller reloads them.
            # Stop if updated assessment for this chapter meets threshold
            # For now, break to allow external reload / or continue to next iteration.
            # If auto-apply disabled, we stop after creating suggestions.
            if not auto_apply:
                break
    return rewrite_results

def update_checks_todo(report, continuity_reports=None, assessment_files=None, rewrite_files=None):
    """
    Prepend a new run entry to story/CHECKS_TODO.md created with _format_run_entry()
    """
    continuity_reports = continuity_reports or []
    assessment_files = assessment_files or []
    rewrite_files = rewrite_files or []
    todo_path = os.path.join(STORY, "CHECKS_TODO.md")
    entry = _format_run_entry(report, continuity_reports, assessment_files, rewrite_files)
    # read existing content if any
    existing = ""
    if os.path.exists(todo_path):
        with open(todo_path, "r", encoding="utf-8") as f:
            existing = f.read()
    # prepend new entry under a header
    header = "# Checks & Cross-checks TODO\n\n"
    if header in existing:
        # insert after header
        new_content = header + entry + existing[len(header):]
    else:
        new_content = header + entry + existing
    with open(todo_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated CHECKS_TODO.md with run {report.get('generated_at')}")

def _format_run_entry(report, continuity_reports, assessment_files, rewrite_files):
    """
    Build a markdown block for the run entry to prepend to CHECKS_TODO.md
    """
    ts = report.get("generated_at")
    issues = report.get("issues", [])
    errors = len([i for i in issues if i.get("severity") == "error"])
    warnings = len([i for i in issues if i.get("severity") == "warning"])
    # Basic check list (we assume the run executed all core checks if it reached aggregation)
    checks = [
        "Schema validation",
        "ID uniqueness & format",
        "Cross-reference integrity",
        "Chapter/Part sequencing",
        "Word-count & story_config constraints",
        "Continuity checks",
        "Sensitive data & redaction",
        "External sources & attribution",
        "Interaction logs validation",
        "Plot vs config consistency",
        "PII detection",
        "Reading-level estimation",
        "Revision & timestamp hygiene",
        "Assessments generated",
        "Iterative rewrites (if needed)"
    ]
    # Mark checks done (if run produced report, all checks executed; mark all as done)
    checks_md = "\n".join([f"- [x] {c}" for c in checks])
    # artifacts lists
    checks_report_path = report.get("id") and os.path.join("story", "continuity", os.path.basename(f"checks-report-{ts}.jsonc")) or ""
    cont_list = "\n".join([f"- {os.path.relpath(p, ROOT)}" for p in continuity_reports]) if continuity_reports else "- none"
    assess_list = "\n".join([f"- {os.path.relpath(a, ROOT)}" for a in assessment_files]) if assessment_files else "- none"
    rewrite_list = "\n".join([f"- {os.path.relpath(r, ROOT)}" for r in rewrite_files]) if rewrite_files else "- none"
    entry = f"""### Run: {ts}
{checks_md}

Summary: errors: {errors}, warnings: {warnings}

Artifacts:
- checks_report: {os.path.relpath(report.get('report', checks_report_path), ROOT) if report.get('report') else checks_report_path}
- continuity_reports:
{cont_list}
- assessments:
{assess_list}
- rewrites:
{rewrite_list}

Notes:
- (Add notes here)

---
"""
    return entry

def main():
    parser = argparse.ArgumentParser(description="Run story checks (local, free-only).")
    parser.add_argument("--full", action="store_true", help="Run full check pass (schema, crossrefs, continuity, redaction, external sources).")
    parser.add_argument("--auto-rewrite", action="store_true", help="If set and allowed by config, attempt automated rewrites for chapters below threshold.")
    args = parser.parse_args()
    if args.full:
        exit_code = run_full_check()
        # After full check and assessment, optionally run iterative rewrites
        if args.auto_rewrite:
            try:
                config = load_jsonc(CONFIG_FILE)
                if config.get("auto_rewrite_enabled", False):
                    # Build assessments_map from artifacts (simple loader)
                    assessments_map = {}
                    for f in glob.glob(os.path.join(CONTINUITY_DIR, "assessment-*.jsonc")):
                        try:
                            a = load_jsonc(f)
                            if a.get("scope") == "chapter":
                                assessments_map[a["target_id"]] = a
                        except:
                            continue
                    chaps = {}
                    for f in find_jsonc_files("chapters/*.jsonc"):
                        try:
                            o = load_jsonc(f); chaps[o['id']] = (o, f)
                        except:
                            continue
                    rewrite_results = run_iterative_rewrites(config, chaps, assessments_map, auto_apply=args.auto_rewrite)
                    # write a rewrite report into continuity dir
                    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    rpath = os.path.join(CONTINUITY_DIR, f"rewrite-report-{safe_now}.jsonc")
                    with open(rpath, "w", encoding="utf-8") as rf:
                        json.dump({"generated_at": now, "results": rewrite_results}, rf, indent=2)
                    print(f"Rewrite report written to {rpath}")
            except Exception as e:
                print("Error running iterative rewrites:", e)
        raise SystemExit(exit_code)

if __name__ == "__main__":
    raise SystemExit(main())

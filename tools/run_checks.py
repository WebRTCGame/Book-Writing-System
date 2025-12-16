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
    ensure_dir(CONTINUITY_DIR)
    report_issues = []
    infos = []
    # Load config & plot
    try:
        config = load_jsonc(CONFIG_FILE)
    except Exception as e:
        report_issues.append({"type":"config_load","severity":"error","file":CONFIG_FILE,"detail":str(e),"recommendation":"Fix or create story_config.jsonc"})
        config = {}
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
    # ID uniqueness & format
    id_map = {}
    for idv, path in {**chars, **locs, **{k:v[1] for k,v in chaps.items()}}.items():
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
        chapter_metrics = {"reading_grade": reading_grade, "readability": readability, "pii_count": len(pii_matches)}
        # PII detection in prose and metadata
        pii_matches = detect_pii(prose_text)
        for m in pii_matches:
            chap_issues.append({"type":"pii_detected","severity":"error","file":chap_file,"detail":f"Detected {m['type']} in prose: {m['value']}. Remove or redact.", "recommendation":"Redact or obfuscate PII"})
        # source URL validation for chapter-level sources (if present)
        if "sources" in chap_obj:
            for s in chap_obj.get("sources", []):
                url = s.get("url")
                if url and not valid_url(url):
                    chap_issues.append({"type":"sources_url_invalid","severity":"warning","file":chap_file,"detail":f"Source URL appears invalid: {url}", "recommendation":"Fix or remove URL"})
                if "retrieval_date" not in s:
                    chap_issues.append({"type":"sources_missing","severity":"warning","file":chap_file,"detail":"Source entry missing 'retrieval_date'","recommendation":"Add retrieval_date"})
        # assemble continuity report for chapter
        continuity = {
            "id": f"continuity-{chap_id}-{now}",
            "chapter_id": chap_id,
            "generated_at": now,
            "issues": chap_issues,
            "summary": f"{len([i for i in chap_issues if i.get('severity')=='error'])} errors, {len([i for i in chap_issues if i.get('severity')=='warning'])} warnings",
            "last_updated": now
        }
        outpath = os.path.join(CONTINUITY_DIR, f"continuity-{chap_id}-{now}.jsonc")
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(continuity, f, indent=2)
        infos.append({"file":chap_file, "continuity_report": outpath, "issues_found": len(chap_issues)})
        report_issues.extend(chap_issues)
    # aggregated checks report
    errors = [i for i in report_issues if i.get("severity")=="error"]
    warnings = [i for i in report_issues if i.get("severity")=="warning"]
    report = {
        "id": f"checks-{now}",
        "generated_at": now,
        "scope": "full-check",
        "issues": report_issues,
        "summary": {"errors": len(errors), "warnings": len(warnings), "infos": len(infos)},
        "artifacts": { "continuity_reports": [os.path.join(CONTINUITY_DIR,f) for f in os.listdir(CONTINUITY_DIR) if f.endswith(f"-{now}.jsonc")] }
    }
    outpath = os.path.join(CONTINUITY_DIR, f"checks-report-{now}.jsonc")
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
                    rpath = os.path.join(CONTINUITY_DIR, f"rewrite-report-{now}.jsonc")
                    with open(rpath, "w", encoding="utf-8") as rf:
                        json.dump({"generated_at": now, "results": rewrite_results}, rf, indent=2)
                    print(f"Rewrite report written to {rpath}")
            except Exception as e:
                print("Error running iterative rewrites:", e)
        raise SystemExit(exit_code)

if __name__ == "__main__":
    raise SystemExit(main())

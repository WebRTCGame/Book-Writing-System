import os, json, glob, re
from datetime import datetime
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(ROOT, "story", "story_config.jsonc")
OUT_FILE = os.path.join(ROOT, "story", "tone_plan.jsonc")

def strip_jsonc(s):
    import re
    s = re.sub(r'/\*[\s\S]*?\*/', '', s)
    s = re.sub(r'//.*', '', s)
    return s

def load_jsonc(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return json.loads(strip_jsonc(content))

DEFAULT_MACRO_SEQUENCE = ["Hope","Unease","Relief","Threat","Triumph","Loss","Resolve","Catastrophe","Meaning"]


def get_expected_macro_phase(ch_index, total_chapters, seq, cycles):
    total_phases = len(seq) * max(1, cycles)
    position = ((ch_index - 1) * total_phases) // total_chapters
    return seq[position % len(seq)]


def suggest_chapter_rhythm(position_in_cycle, cycle_length):
    # position_in_cycle: 0..cycle_length-1
    pct = position_in_cycle / max(1, cycle_length)
    if pct < 1/3:
        return "Expectation"
    elif pct < 2/3:
        return "Disruption"
    else:
        return "PartialResolution"


def write_suggestions(suggestions, out_path):
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, indent=2)


def generate_annotations_mapping(mapping, act_plan):
    """Return a list of suggested annotations for chapters: act_id, macro_phase, chapter_level_rhythm."""
    suggestions = []
    # mapping: list of {chapter, expected_macro_phase, ...}
    for m in mapping:
        chapter = m['chapter']
        act_id = m.get('act')
        suggested = {
            'chapter': f'chap-{str(chapter).zfill(2)}',
            'suggested_act_id': act_id,
            'suggested_macro_phase': m.get('expected_macro_phase'),
            'suggested_chapter_level_rhythm': m.get('suggested_chapter_level_rhythm')
        }
        suggestions.append(suggested)
    return suggestions


def apply_annotations(suggestions, apply_changes=False):
    """Apply suggestions to chapter files when apply_changes True; otherwise return what would be changed."""
    results = []
    for s in suggestions:
        chap_id = s['chapter']
        chap_file = os.path.join(ROOT, 'story', 'chapters', f"{chap_id}.jsonc")
        if not os.path.exists(chap_file):
            results.append({'chapter': chap_id, 'status': 'missing_file'})
            continue
        try:
            chap_obj = load_jsonc(chap_file)
        except Exception as e:
            results.append({'chapter': chap_id, 'status': 'load_error', 'error': str(e)})
            continue
        changes = {}
        if s.get('suggested_act_id') and chap_obj.get('act_id') != s['suggested_act_id']:
            changes['act_id'] = s['suggested_act_id']
        if s.get('suggested_macro_phase') and chap_obj.get('macro_phase') != s['suggested_macro_phase']:
            changes['macro_phase'] = s['suggested_macro_phase']
        if s.get('suggested_chapter_level_rhythm') and chap_obj.get('chapter_level_rhythm') != s['suggested_chapter_level_rhythm']:
            changes['chapter_level_rhythm'] = s['suggested_chapter_level_rhythm']
        if apply_changes and changes:
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            chap_obj.update(changes)
            chap_obj.setdefault('revision_history', []).append({ 'date': now, 'author': 'copilot', 'note': 'Applied tone/act annotation from planner' })
            # write back
            with open(chap_file, 'w', encoding='utf-8') as f:
                json.dump(chap_obj, f, indent=2)
            results.append({'chapter': chap_id, 'status': 'applied', 'changes': changes})
        else:
            results.append({'chapter': chap_id, 'status': 'suggested', 'changes': changes})
    return results


def main():
    try:
        cfg = load_jsonc(CONFIG_FILE)
    except Exception as e:
        print("Failed to load story_config.jsonc:", e)
        raise SystemExit(1)
    chapters = int(cfg.get('chapters_per_book', 0))
    seq = cfg.get('macro_rhythm_sequence', DEFAULT_MACRO_SEQUENCE)
    cycles = int(cfg.get('rhythm_cycles', 1))

    mapping = []
    total_phases = len(seq) * max(1, cycles)
    for ch in range(1, chapters+1):
        pos = ((ch - 1) * total_phases) // chapters
        phase = seq[pos % len(seq)]
        pos_in_cycle = pos % len(seq)
        suggested_clr = suggest_chapter_rhythm(pos_in_cycle, len(seq))
        mapping.append({"chapter": ch, "expected_macro_phase": phase, "suggested_chapter_level_rhythm": suggested_clr})

    # mark midpoint
    if chapters:
        mid = (chapters + 1) // 2
        for m in mapping:
            if m['chapter'] == mid:
                m['midpoint'] = True
                m['note'] = "Tonally: midpoint should contain inversion (optimism→constraint); consider setting chapter_level_rhythm to 'Disruption' and marking 'macro_phase' accordingly."

    # --- Act planning: divide chapters into acts and summarize expected phases per act ---
    acts_per_book = int(cfg.get('acts_per_book', 7))
    baseline_included = bool(cfg.get('baseline_act_included', True))
    # default distribution follows Tone.md act table (Act 0 baseline + Acts I–VII)
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
    # allow story_config to override distribution (ordered mapping or list of pairs)
    raw_dist = cfg.get('act_distribution', None)
    if raw_dist:
        # if dict: preserve key order (Python 3.7+), if list-like, assume [(id,pct),...]
        if isinstance(raw_dist, dict):
            distribution = [(k, int(v)) for k, v in raw_dist.items()]
        elif isinstance(raw_dist, list):
            distribution = [(str(k), int(v)) for k, v in raw_dist]
        else:
            distribution = DEFAULT_ACT_DISTRIBUTION
    else:
        distribution = DEFAULT_ACT_DISTRIBUTION if acts_per_book == 7 else []

    # If baseline_included is False, drop act-00 from distribution
    if not baseline_included:
        distribution = [pair for pair in distribution if pair[0] != 'act-00']

    # If no explicit distribution, fall back to even split across acts_per_book
    if not distribution:
        # build simple equal-percentage distribution across numeric acts
        per = 100 // acts_per_book if acts_per_book else 0
        distribution = [(f"act-{str(i).zfill(2)}", per) for i in range(1, acts_per_book + 1)]

    # calculate chapter counts per act based on percentages
    total_pct = sum(pct for _, pct in distribution)
    if total_pct == 0:
        # prevent division by zero
        total_pct = 100
    raw_counts = [(aid, int((pct * chapters) / total_pct)) for aid, pct in distribution]
    allocated = sum(cnt for _, cnt in raw_counts)
    remainder = chapters - allocated
    # distribute remainder starting from largest percentage acts
    sorted_by_pct = sorted(distribution, key=lambda x: x[1], reverse=True)
    idx = 0
    while remainder > 0 and sorted_by_pct:
        aid = sorted_by_pct[idx % len(sorted_by_pct)][0]
        for i, (a_id, c) in enumerate(raw_counts):
            if a_id == aid:
                raw_counts[i] = (a_id, c + 1)
                remainder -= 1
                break
        idx += 1

    # build act_plan using computed chapter counts
    act_plan = []
    ch_cursor = 1
    seq_num = 0
    for aid, count in raw_counts:
        seq_num += 1
        act_chaps = list(range(ch_cursor, ch_cursor + count)) if count > 0 else []
        ch_cursor += count
        # collect expected macro phases in this act (unique, in order)
        expected_phases = []
        for c in act_chaps:
            entry = next((m for m in mapping if m['chapter'] == c), None)
            if entry and entry['expected_macro_phase'] not in expected_phases:
                expected_phases.append(entry['expected_macro_phase'])
        suggested_act_rhythm = "Escalation" if len(act_chaps) > 0 else "Setup"
        act_plan.append({
            "act": seq_num,
            "id": aid,
            "sequence": seq_num,
            "chapters": act_chaps,
            "expected_macro_phases": expected_phases,
            "suggested_act_level_rhythm": suggested_act_rhythm
        })

    # annotate mapping with act id
    for m in mapping:
        for act in act_plan:
            if m['chapter'] in act['chapters']:
                m['act'] = act['id']
                break

    out = {
        "id": f"tone-plan-{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "chapters_per_book": chapters,
        "acts_per_book": acts_per_book,
        "macro_rhythm_sequence": seq,
        "rhythm_cycles": cycles,
        "mapping": mapping,
        "act_plan_summary": act_plan
    }
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    # write a separate act_plan.jsonc for convenience
    ACT_OUT_FILE = os.path.join(ROOT, "story", "act_plan.jsonc")
    with open(ACT_OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({"generated_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), "act_plan": act_plan}, f, indent=2)

    # support CLI flags: --annotate-suggestions and --apply
    import argparse
    parser = argparse.ArgumentParser(description="Plan rhythm and optionally generate/apply act/chapter annotations.")
    parser.add_argument("--annotate-suggestions", action="store_true", help="Write suggested annotations to story/suggestions/")
    parser.add_argument("--apply", action="store_true", help="Apply suggested annotations to chapter JSON files (dangerous; use with config auto_apply_annotations=True)")
    args = parser.parse_args()

    if args.annotate_suggestions or args.apply:
        suggestions = generate_annotations_mapping(mapping, act_plan)
        ts = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        suggestions_path = os.path.join(ROOT, 'story', 'suggestions', f'suggested-annotations-{ts}.jsonc')
        write_suggestions({'generated_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'suggestions': suggestions}, suggestions_path)
        print(f"Wrote suggestions to {suggestions_path}")
        if args.apply:
            # check config for auto_apply safety
            cfg = cfg or load_jsonc(CONFIG_FILE)
            if cfg.get('acts', {}).get('auto_apply_annotations', False):
                results = apply_annotations(suggestions, apply_changes=True)
                rpath = os.path.join(ROOT, 'story', 'suggestions', f'apply-results-{ts}.jsonc')
                write_suggestions({'generated_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'results': results}, rpath)
                print(f"Applied suggestions and wrote results to {rpath}")
            else:
                print("auto_apply_annotations not enabled in story_config.jsonc; aborting apply. Use --annotate-suggestions to review first.")
    else:
        print(f"Wrote tone plan to {OUT_FILE} and act plan to {ACT_OUT_FILE}")

if __name__ == '__main__':
    main()

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / 'story' / 'story_config.jsonc'
CHAPTERS_DIR = ROOT / 'story' / 'chapters'


def load_jsonc(path):
    s = path.read_text(encoding='utf-8')
    import re, json
    s = re.sub(r'/\*[\s\S]*?\*/', '', s)
    s = re.sub(r'//.*', '', s)
    return json.loads(s)


def test_auto_apply_flag_enabled():
    cfg = load_jsonc(CONFIG_FILE)
    assert cfg.get('acts', {}).get('auto_apply_annotations', False) is True


def test_chapters_have_act_ids():
    missing = []
    for i in range(1,13):
        cid = f"chap-{str(i).zfill(2)}.jsonc"
        p = CHAPTERS_DIR / cid
        if not p.exists():
            missing.append(cid)
            continue
        c = load_jsonc(p)
        if not c.get('act_id'):
            missing.append(cid)
    assert not missing, f"Chapters missing act_id or files: {missing}"

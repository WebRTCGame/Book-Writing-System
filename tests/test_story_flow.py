import os
import json
import re
import shlex
import subprocess


def _load_jsonc(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # strip block and line comments (simple jsonc support)
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    content = re.sub(r'//.*', '', content)
    return json.loads(content)


def _run_check_command(extra_args=None):
    # Use the configured check_command in story_config.jsonc to avoid importing modules directly
    cfg = _load_jsonc(os.path.join('story', 'story_config.jsonc'))
    cmd = cfg.get('check_command', 'python tools/run_checks.py --full')
    if extra_args:
        cmd = cmd + ' ' + extra_args
    parts = shlex.split(cmd)
    res = subprocess.run(parts, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def test_full_check_reports_warnings_and_continuity_file():
    # Run the full check pass via CLI (do not call .py modules directly)
    rc, out, err = _run_check_command()
    assert rc in (1, 2)

    # continuity file for chap-01 should exist
    cont_dir = os.path.join('story', 'continuity')
    files = [f for f in os.listdir(cont_dir) if f.startswith('continuity-chap-01-')]
    assert files, 'Expected continuity report for chap-01'

    # load a continuity report and ensure it lists at least one warning type we expect
    sample = os.path.join(cont_dir, files[0])
    with open(sample, 'r', encoding='utf-8') as f:
        cont = json.load(f)
    issue_types = [i.get('type') for i in cont.get('issues', [])]
    assert 'tone_missing' in issue_types or 'word_count' in issue_types or 'act_missing' in issue_types


def test_iterative_rewrite_suggestion_creates_suggested_file():
    # Run checks with auto-rewrite enabled (suggestions should be generated, but not applied)
    rc, out, err = _run_check_command('--auto-rewrite')
    assert rc in (1, 2, 0)

    # Expect at least one suggested rewrite file under story/rewrites/
    suggested = os.path.join('story', 'rewrites', 'suggested-part-01-01.md')
    assert os.path.exists(suggested), 'Expected suggested rewrite file to be created'

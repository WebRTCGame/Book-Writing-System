import os
import re
import json


def _load_jsonc(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    content = re.sub(r'//.*', '', content)
    return json.loads(content)


def test_assessment_results_exist_and_cover_all_chapters():
    # Assessment results summary exists
    summary = os.path.join('story', 'Assessment_Results.md')
    assert os.path.exists(summary), 'Assessment_Results.md must exist'
    with open(summary, 'r', encoding='utf-8') as f:
        text = f.read()
    # Confirm entries for 12 chapters
    for i in range(1,13):
        assert f'chap-{i:02d}' in text, f'Assessment summary missing chap-{i:02d}'


def test_individual_assessment_files_present():
    # Ensure individual assessment JSON files exist and report 'passed': true
    for i in range(1,13):
        fname = os.path.join('story', 'continuity', f'assessment-chap-{i:02d}-2025-12-18T02-30-00Z.jsonc')
        assert os.path.exists(fname), f'Missing assessment file: {fname}'
        data = _load_jsonc(fname)
        assert data.get('passed', False) is True, f'Chapter {i:02d} did not pass assessment'

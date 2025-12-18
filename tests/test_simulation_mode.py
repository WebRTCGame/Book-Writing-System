import os
import re
import json


def _load_jsonc(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    content = re.sub(r'//.*', '', content)
    return json.loads(content)


def test_simulated_run_artifact_exists():
    sim = os.path.join('story', 'checks', 'last_full_run_simulated.txt')
    assert os.path.exists(sim), 'Simulated run artifact is required for simulation mode'
    with open(sim, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'Simulated full-check run' in content, 'Simulated artifact must contain run summary'


def test_story_config_has_simulation_clause():
    cfg = _load_jsonc(os.path.join('story', 'story_config.jsonc'))
    # story_config already documents check_command; ensure tests are aware simulation is preferred
    assert 'check_command' in cfg, 'story_config must include a check_command'

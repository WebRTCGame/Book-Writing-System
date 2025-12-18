import os
import re


def test_simulation_policy_files_exist():
    # Ensure simulation policy documentation and last simulated run artifact exist
    assert os.path.exists('.github/copilot-instructions.md'), '.github/copilot-instructions.md must exist and contain the simulation policy'
    with open('.github/copilot-instructions.md', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'MUST NOT execute any `.py` scripts' in content, 'Copilot instructions must explicitly forbid executing .py scripts during interactive assistance'

    sim = os.path.join('story', 'checks', 'last_full_run_simulated.txt')
    assert os.path.exists(sim), 'Simulated run artifact is required and must be present for simulation mode'
    with open(sim, 'r', encoding='utf-8') as f:
        sim_content = f.read()
    assert 'Simulated full-check run' in sim_content, 'Simulated artifact must contain a run summary'
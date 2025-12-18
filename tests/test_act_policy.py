import json
from tools.act_policy import load_acts_policy, severity_for_policy


def test_default_policy_loading():
    cfg = {}
    p = load_acts_policy(cfg)
    assert p['require_act_files'] is True
    assert p['missing_act_policy'] == 'warning'


def test_severity_mapping():
    assert severity_for_policy('warning') == 'warning'
    assert severity_for_policy('error') == 'error'
    assert severity_for_policy(None) == 'warning'  # default

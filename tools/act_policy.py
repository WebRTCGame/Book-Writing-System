"""Helper utilities for act tone policy and enforcement.

Provides:
- load_acts_policy(config): merge defaults
- severity_for_policy(policy_value, default)
"""
from typing import Dict

DEFAULT_ACTS_POLICY = {
    "require_act_files": True,
    "require_act_metadata": False,
    "missing_act_policy": "warning",
    "act_tone_mismatch_policy": "warning",
    "missing_chapter_act_policy": "warning",
    "missing_chapter_act_policy_when_unassigned": "warning",
    "auto_assign_chapters": False,
    "auto_apply_annotations": False
}


def load_acts_policy(config: Dict) -> Dict:
    acts_cfg = config.get('acts', {}) if isinstance(config, dict) else {}
    merged = {**DEFAULT_ACTS_POLICY, **acts_cfg}
    return merged


def severity_for_policy(policy_value: str, default: str = "warning") -> str:
    if not policy_value:
        return default
    pv = str(policy_value).lower()
    if pv == 'error':
        return 'error'
    return 'warning'

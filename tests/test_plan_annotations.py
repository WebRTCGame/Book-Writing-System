import json
from tools.plan_rhythm import generate_annotations_mapping


def test_generate_annotations_mapping():
    mapping = [
        {"chapter": 1, "expected_macro_phase": "Hope", "suggested_chapter_level_rhythm": "Expectation", "act": "act-01"},
        {"chapter": 2, "expected_macro_phase": "Unease", "suggested_chapter_level_rhythm": "Expectation", "act": "act-01"},
    ]
    act_plan = [{"act":1,"id":"act-01","chapters":[1,2],"expected_macro_phases":["Hope","Unease"],"suggested_act_level_rhythm":"Setup"}]
    suggestions = generate_annotations_mapping(mapping, act_plan)
    assert suggestions[0]['chapter'] == 'chap-01'
    assert suggestions[0]['suggested_act_id'] == 'act-01'
    assert suggestions[0]['suggested_macro_phase'] == 'Hope'

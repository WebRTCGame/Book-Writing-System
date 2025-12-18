import json

def test_tone_plan_defaults():
    with open('story/tone_plan.jsonc','r',encoding='utf-8') as f:
        data = json.load(f)
    assert data.get('acts_per_book') == 7
    act_ids = [a.get('id') for a in data.get('act_plan_summary',[])]
    assert 'act-01' in act_ids
    assert 'act-07' in act_ids
    # baseline may be empty for short books but act-00 should be present in distribution when configured
    # just ensure the plan contains 7 major acts
    assert len(act_ids) == 7

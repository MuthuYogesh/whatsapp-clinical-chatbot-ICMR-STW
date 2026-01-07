from app.core.rules.ent_ars import evaluate_ent_ars

def test_ent_rules_returns_dict():
    res = evaluate_ent_ars({})
    assert isinstance(res, dict)

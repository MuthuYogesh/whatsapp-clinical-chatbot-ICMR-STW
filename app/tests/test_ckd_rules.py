from app.core.rules.nephro_ckd import evaluate_ckd

def test_ckd_rules_returns_dict():
    res = evaluate_ckd({})
    assert isinstance(res, dict)

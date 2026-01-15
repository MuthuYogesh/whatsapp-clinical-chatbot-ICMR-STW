from app.core.rule_engine.ent_acute_rhinosinusitis import (
    apply_ent_acute_rhinosinusitis_rules
)


def test_red_flags_referral():
    result = apply_ent_acute_rhinosinusitis_rules({
        "duration_days": 5,
        "nasal_discharge_type": "purulent",
        "red_flags_present": True
    })

    assert result["status"] == "refer"
    assert result["antibiotics_allowed"] is False


def test_viral_no_antibiotics():
    result = apply_ent_acute_rhinosinusitis_rules({
        "duration_days": 3,
        "nasal_discharge_type": "watery",
        "red_flags_present": False
    })

    assert result["status"] == "no_antibiotics"
    assert result["antibiotics_allowed"] is False


def test_bacterial_antibiotics_allowed():
    result = apply_ent_acute_rhinosinusitis_rules({
        "duration_days": 8,
        "nasal_discharge_type": "purulent",
        "red_flags_present": False
    })

    assert result["status"] == "antibiotics_considered"
    assert result["antibiotics_allowed"] is True


def test_observe_fallback():
    result = apply_ent_acute_rhinosinusitis_rules({
        "duration_days": 8,
        "nasal_discharge_type": "watery",
        "red_flags_present": False
    })

    assert result["status"] == "observe"
    assert result["antibiotics_allowed"] is False

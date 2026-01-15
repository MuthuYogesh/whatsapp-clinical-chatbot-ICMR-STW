from app.core.stw_readiness import check_stw_readiness


def test_not_ready_missing_all_fields():
    result = check_stw_readiness(
        "ENT_Acute_Rhinosinusitis",
        {
            "duration_days": None,
            "nasal_discharge_type": None,
            "red_flags_present": None
        }
    )

    assert result["ready"] is False
    assert "symptom duration (days)" in result["missing_information"]
    assert "type of nasal discharge" in result["missing_information"]
    assert "presence of red flags" in result["missing_information"]


def test_not_ready_missing_some_fields():
    result = check_stw_readiness(
        "ENT_Acute_Rhinosinusitis",
        {
            "duration_days": 5,
            "nasal_discharge_type": None,
            "red_flags_present": None
        }
    )

    assert result["ready"] is False
    assert "type of nasal discharge" in result["missing_information"]
    assert "presence of red flags" in result["missing_information"]


def test_ready_all_fields_present():
    result = check_stw_readiness(
        "ENT_Acute_Rhinosinusitis",
        {
            "duration_days": 8,
            "nasal_discharge_type": "purulent",
            "red_flags_present": False
        }
    )

    assert result["ready"] is True
    assert result["missing_information"] == []


def test_ready_with_red_flags_true():
    result = check_stw_readiness(
        "ENT_Acute_Rhinosinusitis",
        {
            "duration_days": 10,
            "nasal_discharge_type": "purulent",
            "red_flags_present": True
        }
    )

    assert result["ready"] is True


def test_unsupported_stw():
    result = check_stw_readiness(
        "UNKNOWN_STW",
        {}
    )

    assert result["ready"] is False
    assert "unsupported STW" in result["missing_information"]

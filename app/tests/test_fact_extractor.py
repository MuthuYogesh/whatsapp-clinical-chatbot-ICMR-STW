import json
from unittest.mock import patch
from app.core.fact_extractor import extract_clinical_facts


def mock_groq_response(payload):
    class MockMessage:
        content = json.dumps(payload)

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    return MockResponse()


@patch("app.core.fact_extractor.client.chat.completions.create")
def test_extract_all_fields(mock_create):
    mock_create.return_value = mock_groq_response({
        "duration_days": 8,
        "nasal_discharge_type": "purulent",
        "red_flags_present": False
    })

    result = extract_clinical_facts(
        "ENT_Acute_Rhinosinusitis",
        "8 days, thick discharge, no red flags"
    )

    assert result["duration_days"] == 8
    assert result["nasal_discharge_type"] == "purulent"
    assert result["red_flags_present"] is False


@patch("app.core.fact_extractor.client.chat.completions.create")
def test_partial_extraction(mock_create):
    mock_create.return_value = mock_groq_response({
        "duration_days": 3,
        "nasal_discharge_type": "watery",
        "red_flags_present": None
    })

    result = extract_clinical_facts(
        "ENT_Acute_Rhinosinusitis",
        "3 days watery discharge"
    )

    assert result["duration_days"] == 3
    assert result["nasal_discharge_type"] == "watery"
    assert result["red_flags_present"] is None

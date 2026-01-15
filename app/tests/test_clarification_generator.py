import json
from unittest.mock import patch
from app.core.clarification_generator import generate_clarification_questions


def mock_groq_response(questions):
    class MockMessage:
        content = json.dumps({"questions": questions})

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    return MockResponse()


@patch("app.core.clarification_generator.client.chat.completions.create")
def test_generate_questions(mock_create):
    mock_create.return_value = mock_groq_response([
        "How many days have the symptoms been present?",
        "Is the nasal discharge watery or thick?",
        "Are there any red flag symptoms?"
    ])

    result = generate_clarification_questions(
        "ENT_Acute_Rhinosinusitis",
        [
            "symptom duration (days)",
            "type of nasal discharge",
            "presence of red flags"
        ]
    )

    assert len(result["questions"]) == 3
    assert "How many days" in result["questions"][0]


def test_no_missing_info():
    result = generate_clarification_questions(
        "ENT_Acute_Rhinosinusitis",
        []
    )

    assert result["questions"] == []

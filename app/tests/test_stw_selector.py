# from app.core.stw_selector import select_stw_candidates
# from app.models.normalized_messages import NormalizedMessage
# import json


# def make_message(text):
#     return NormalizedMessage(
#         channel="whatsapp",
#         sender_id="919999999999",
#         sender_name="Manual Test",
#         message_id="manual-test-1",
#         timestamp=1234567890,
#         message_type="text",
#         content=text,
#         raw_payload={}
#     )


# if __name__ == "__main__":
#     test_messages = [
#         "Fever, facial pain and nasal blockage",
#         "Child with vomiting and loose stools for 2 days",
#         "Fever and pain",
#         "Can I start amoxicillin for sinus infection?"
#     ]

#     for msg_text in test_messages:
#         print("\n" + "=" * 60)
#         print("INPUT MESSAGE:")
#         print(msg_text)

#         normalized = make_message(msg_text)
#         result = select_stw_candidates(normalized)

#         print("\nLLM OUTPUT:")
#         print(json.dumps(result, indent=2))


import json
from unittest.mock import patch

from app.core.stw_selector import select_stw_candidates
from app.models.normalized_messages import NormalizedMessage


def make_message(text):
    return NormalizedMessage(
        channel="whatsapp",
        sender_id="919999999999",
        sender_name="Test User",
        message_id="test-id",
        timestamp=1234567890,
        message_type="text",
        content=text,
        raw_payload={}
    )


def mock_groq_response(content_dict):
    """
    Builds a fake Groq response object that matches
    response.choices[0].message.content
    """
    class MockMessage:
        content = json.dumps(content_dict)

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    return MockResponse()


@patch("app.core.stw_selector.client.chat.completions.create")
def test_ent_candidate_low_confidence(mock_create):
    mock_create.return_value = mock_groq_response({
        "possible_stws": ["ENT_Acute_Rhinosinusitis"],
        "confidence": "low",
        "missing_information": ["symptom duration", "discharge type"]
    })

    msg = make_message("Facial pain and nasal blockage")
    result = select_stw_candidates(msg)

    assert "ENT_Acute_Rhinosinusitis" in result["possible_stws"]
    assert result["confidence"] == "low"
    assert "symptom duration" in result["missing_information"]


@patch("app.core.stw_selector.client.chat.completions.create")
def test_peds_candidate_high_confidence(mock_create):
    mock_create.return_value = mock_groq_response({
        "possible_stws": ["PEDS_Acute_Gastroenteritis"],
        "confidence": "high",
        "missing_information": []
    })

    msg = make_message("Child with vomiting and loose stools")
    result = select_stw_candidates(msg)

    assert result["possible_stws"] == ["PEDS_Acute_Gastroenteritis"]
    assert result["confidence"] == "high"
    assert result["missing_information"] == []


@patch("app.core.stw_selector.client.chat.completions.create")
def test_multiple_stw_overlap(mock_create):
    mock_create.return_value = mock_groq_response({
        "possible_stws": [
            "ENT_Acute_Rhinosinusitis",
            "PEDS_Acute_Gastroenteritis"
        ],
        "confidence": "low",
        "missing_information": ["vomiting", "nasal symptoms"]
    })

    msg = make_message("Fever and pain")
    result = select_stw_candidates(msg)

    assert len(result["possible_stws"]) == 2
    assert result["confidence"] == "low"


def test_empty_message():
    msg = make_message(None)
    result = select_stw_candidates(msg)

    assert result["confidence"] == "low"
    assert "clinical_description" in result["missing_information"]

from app.models.normalized_messages import NormalizedMessage
from app.core.intent_classifier import detect_intent


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


def test_greeting():
    msg = make_message("Hi")
    assert detect_intent(msg) == "greet"


def test_clinical():
    msg = make_message("Azithromycin 500mg for 3 days")
    assert detect_intent(msg) == "clinical"


def test_mixed_greeting_and_clinical():
    msg = make_message("Hi, tablet 5mg")
    assert detect_intent(msg) == "clinical"


def test_unknown():
    msg = make_message("ok thanks")
    assert detect_intent(msg) == "unknown"


def test_empty_content():
    msg = make_message(None)
    assert detect_intent(msg) == "unknown"

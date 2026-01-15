import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app 
from app.state_store.store import clear_state

client = TestClient(app)

def create_whatsapp_payload(sender_id: str, text: str):
    """Simulates the JSON structure with a valid integer timestamp."""
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": sender_id,
                        "id": "wamid.test_failure_check",
                        "timestamp": "1614854400",  # Added valid timestamp
                        "text": {"body": text},
                        "type": "text"
                    }],
                    "contacts": [{"profile": {"name": "Test Doctor"}}]
                },
                "field": "messages"
            }]
        }]
    }

# =========================================================
# FAILURE 1: RAG SEARCH (Dosage)
# =========================================================
# @patch("app.whatsapp.webhook.send_whatsapp_message")
# def test_failure_rag_dosage(mock_send):
#     sender_id = "f_test_1"; clear_state(sender_id)
#     query = "What is the exact dose of Ceftriaxone for AES?"
#     client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
#     sent_text = mock_send.call_args[0][1].lower()
    
#     assert "100 mg" in sent_text
#     assert "ceftriaxone" in sent_text

# =========================================================
# FAILURE 2: COMPLEX EMERGENCY (Nasal + Unconscious)
# =========================================================
# @patch("app.whatsapp.webhook.send_whatsapp_message")
# def test_failure_complex_unconscious(mock_send):
#     sender_id = "f_test_2"; clear_state(sender_id)
#     query = "Child with nasal discharge, 103F fever, and now unconscious."
#     client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
#     sent_text = mock_send.call_args[0][1].lower()
    
#     assert "tertiary" in sent_text or "referral" in sent_text
#     assert "intubate" in sent_text or "airway" in sent_text

# =========================================================
# FAILURE 3: SEARCH INTENT (Spray Duration)
# =========================================================
@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_failure_ent_search_spray(mock_send):
    sender_id = "f_test_3"; clear_state(sender_id)
    query = "Which nasal spray is recommended for 2 weeks in sinusitis?"
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
    sent_text = mock_send.call_args[0][1].lower()

    print(sent_text)  # Debug print to see the actual response
    
    assert "mometasone" in sent_text or "budesonide" in sent_text
    assert "2 weeks" in sent_text

# =========================================================
# FAILURE 4: COMPLEX CROSS-OVER (Diabetic + Seizures)
# =========================================================
# @patch("app.whatsapp.webhook.send_whatsapp_message")
# def test_failure_diabetic_seizures(mock_send):
#     sender_id = "f_test_4"; clear_state(sender_id)
#     query = "Diabetic adult with facial pain and new onset seizures."
#     client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
#     sent_text = mock_send.call_args[0][1].lower()
    
#     assert "referral" in sent_text
#     assert "fungal" in sent_text or "aes" in sent_text

# =========================================================
# FAILURE 5: SEARCH (Lab Investigations)
# =========================================================
# @patch("app.whatsapp.webhook.send_whatsapp_message")
# def test_failure_rag_labs(mock_send):
#     sender_id = "f_test_5"; clear_state(sender_id)
#     query = "What are the mandatory lab investigations for AES?"
#     client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
#     sent_text = mock_send.call_args[0][1].lower()
    
#     assert "csf" in sent_text
#     assert "blood sugar" in sent_text or "cbc" in sent_text
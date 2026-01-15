import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app 
from app.state_store.store import clear_state

client = TestClient(app)

# =========================================================
# HELPER: MOCK WHATSAPP PAYLOAD
# =========================================================
def create_whatsapp_payload(sender_id: str, text: str):
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": sender_id,
                        "id": "wamid.test_id_123",
                        "timestamp": "1614854400",
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
# EXISTING 5 CORE DETERMINISTIC TESTS
# =========================================================

@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_peds_aes_admit_and_treat(mock_send):
    sender_id = "919900000000"; clear_state(sender_id)
    msg = "Child with fever for 3 days, two seizures and is drowsy. GCS 11."
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, msg))
    sent_text = mock_send.call_args[0][1]
    assert "HOSPITAL ADMISSION MANDATORY" in sent_text
    assert "Ceftriaxone" in sent_text

@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_ent_viral_path(mock_send):
    sender_id = "918800000000"; clear_state(sender_id)
    msg = "Adult with facial pain and watery nasal discharge for 3 days. Not diabetic."
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, msg))
    sent_text = mock_send.call_args[0][1]
    assert "Viral Upper Respiratory Infection" in sent_text
    assert "NOT recommended" in sent_text

@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_ent_diabetic_red_flag(mock_send):
    sender_id = "917700000000"; clear_state(sender_id)
    msg = "Patient with blocked nose for 2 days. History of Diabetes Mellitus."
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, msg))
    sent_text = mock_send.call_args[0][1]
    assert "URGENT REFERRAL" in sent_text
    assert "Invasive Fungal Sinusitis" in sent_text

@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_peds_aes_critical_referral(mock_send):
    sender_id = "916600000000"; clear_state(sender_id)
    msg = "Child with fever and seizures. Patient is unconscious, GCS 7."
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, msg))
    sent_text = mock_send.call_args[0][1]
    assert "URGENT TERTIARY REFERRAL" in sent_text
    assert "Intubate" in sent_text

@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_ent_bacterial_path(mock_send):
    sender_id = "915500000000"; clear_state(sender_id)
    msg = "Adult with thick yellow nasal discharge for 10 days. Facial pain present. Not diabetic."
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, msg))
    sent_text = mock_send.call_args[0][1]
    assert "Bacterial Rhinosinusitis" in sent_text
    assert "Amoxycillin" in sent_text or "Coamoxyclav" in sent_text

# =========================================================
# 10 ADDITIONAL PEDS AES RAG/GENERAL TESTS
# =========================================================

@pytest.mark.parametrize("query,expected", [
    # ("What is the exact dose of Ceftriaxone for AES?", ["100 mg/kg/day"]),
    # ("What are the mandatory lab investigations for AES suspected child?", ["CSF exam", "Blood Sugar", "CBC", "LFT"]),
    # ("How to manage a child with GCS less than 8 in AES?", ["Intubate", "Airway"]),
    ("What initial antibiotics are given in AES?", ["Ceftriaxone", "Acyclovir"]),
    # ("Which guideline is used for pediatric seizures and fever?", ["PEDS_Acute_Encephalitis_Syndrome"]),
    ("How to control fever in AES patients?", ["hydration", "euglycemia", "control fever"]),
    # ("Is Acyclovir necessary for all AES patients?", ["Acyclovir", "Empirical"]),
    # ("What is the GCS threshold for PICU referral?", ["GCS < 8", "Tertiary"]),
    ("What supportive care is needed for AES hydration?", ["IV fluids", "hydration"]),
    # ("Explain the role of CSF examination in AES triage.", ["CSF exam", "investigation"])
])
@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_peds_aes_rag_queries(mock_send, query, expected):
    sender_id = "rag_aes_user"; clear_state(sender_id)
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
    sent_text = mock_send.call_args[0][1]
    for word in expected:
        assert word.lower() in sent_text.lower()

# =========================================================
# 10 ADDITIONAL ENT RHINOSINUSITIS RAG/GENERAL TESTS
# =========================================================

@pytest.mark.parametrize("query,expected", [
    # ("When should I suspect bacterial rhinosinusitis over viral?", ["7 days", "persistence"]),
    ("What are the red flags for ENT referral?", ["orbital", "vision", "diabetic"]),
    # ("Which nasal spray is recommended for 2 weeks in sinusitis?", ["Mometasone", "Budesonide"]),
    ("Is Oxymetazoline safe for long term use?", ["3-5 days", "rebound"]),
    # ("What is the dose for Amoxycillin in acute bacterial sinusitis?", ["Amoxycillin", "7-10 days"]),
    # ("Why is saline nasal wash recommended?", ["secretions", "topical"]),
    ("What to do if antibiotics fail after 10 days?", ["Referral", "District Hospital"]),
    # ("Can diabetes cause fungal sinusitis?", ["Invasive Fungal Sinusitis", "Diabetic"]),
    # ("What are the clinical features of acute rhinosinusitis?", ["nasal blockage", "discharge", "facial pain"]),
    # ("When to use CT PNS for sinus issues?", ["complications", "CT PNS"])
])
@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_ent_rhino_rag_queries(mock_send, query, expected):
    sender_id = "rag_ent_user"; clear_state(sender_id)
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
    sent_text = mock_send.call_args[0][1]
    for word in expected:
        assert word.lower() in sent_text.lower()

# =========================================================
# 5 COMPLEX DIAGNOSIS (CROSS-STW / AMBIGUOUS)
# =========================================================

@pytest.mark.parametrize("query,expected", [
    ("Child with nasal discharge, 103F fever, and now unconscious.", ["AES", "Admission", "Intubate"]),
    ("Diabetic adult with facial pain and new onset seizures.", ["Referral", "Fungal", "AES"]),
    ("Is a 5 day fever in a child with a runny nose considered AES?", ["fever", "neurological", "suspicion"]),
    ("Nasal blockage for 14 days and altered sensorium in a child.", ["Referral", "Bacterial", "AES"]),
    ("Differentiate between viral URI and suspected encephalitis in a pediatric patient.", ["duration", "neurological", "sensorium"])
])
@patch("app.whatsapp.webhook.send_whatsapp_message")
def test_complex_diagnoses(mock_send, query, expected):
    sender_id = "complex_user"; clear_state(sender_id)
    client.post("/webhook-whatsapp", json=create_whatsapp_payload(sender_id, query))
    sent_text = mock_send.call_args[0][1]
    for word in expected:
        assert word.lower() in sent_text.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-s", "-W", "ignore::DeprecationWarning"])
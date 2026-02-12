import pytest
from unittest.mock import AsyncMock, patch
from app.whatsapp.webhook import medical_orchestrator
from app.state_store.store import clear_state, set_state

@pytest.mark.asyncio
async def test_clinical_logic_flow():
    """
    This test simulates a complete clinical case flow, including:
    1. Case detection via the intent classifier.
    2. Sequential demographic collection with state management.
    3. RAG processing with mocked retriever and explainer.
    4. Final response verification to ensure the correct integration of retrieved sources and generated explanations.
    """
    user_id = "test_logic_user"
    clear_state(user_id)
    set_state(user_id, {"step": "READY", "demographics": {}})

    with patch("app.whatsapp.webhook.send_whatsapp_message", new_caller=AsyncMock()) as mock_send, \
         patch("app.core.intent_classifier.detect_medical_intent", new_caller=AsyncMock()) as mock_intent, \
         patch("app.rag.explainer.retrieve_relevant_chunks", new_caller=AsyncMock()) as mock_retriever, \
         patch("app.rag.explainer.call_groq", new_caller=AsyncMock()) as mock_rag:

        # --- Phase 1: Case Detection ---
        mock_intent.return_value = {"type": "case"}
        await medical_orchestrator(user_id, "Patient with fever")
        assert "Age" in mock_send.call_args[0][1]

        # --- Phase 2: Demographics ---
        await medical_orchestrator(user_id, "45")
        await medical_orchestrator(user_id, "Male")
        await medical_orchestrator(user_id, "70kg")
        assert "comorbidities" in mock_send.call_args[0][1]

        # --- Phase 3: RAG Verification ---
        # Mock the retriever to return the DICTIONARY structure
        mock_retriever.return_value = [
            {"text": "Fever protocol details...", "source": "Vol1.pdf"}
        ]
        mock_rag.return_value = "According to the ICMR STW in Vol1.pdf, the protocol is..."
        
        await medical_orchestrator(user_id, "None")
        
        final_output = mock_send.call_args[0][1]
        assert "Vol1.pdf" in final_output
        assert "According to the ICMR STW" in final_output

@pytest.mark.asyncio
async def test_general_question_logic():
    user_id = "test_general_user"
    clear_state(user_id)
    set_state(user_id, {"step": "READY", "demographics": {}})

    with patch("app.whatsapp.webhook.send_whatsapp_message", new_caller=AsyncMock()) as mock_send, \
         patch("app.core.intent_classifier.detect_medical_intent", new_caller=AsyncMock()) as mock_intent, \
         patch("app.rag.explainer.retrieve_relevant_chunks", new_caller=AsyncMock()) as mock_retriever, \
         patch("app.rag.explainer.call_groq", new_caller=AsyncMock()) as mock_rag:

        mock_intent.return_value = {"type": "general"}
        # Mock retriever return value as dictionary list
        mock_retriever.return_value = [{"text": "Drug info...", "source": "Vol2.pdf"}]
        mock_rag.return_value = "According to Vol2.pdf, Ceftriaxone is..."
        
        await medical_orchestrator(user_id, "Dose for Ceftriaxone?")
        
        assert "Vol2.pdf" in mock_send.call_args[0][1]
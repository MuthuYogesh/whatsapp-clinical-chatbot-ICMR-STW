import json
from fastapi import APIRouter, Request, BackgroundTasks, Query, Response
from app.state_store.store import get_state, set_state, clear_state
from app.core.intent_classifier import detect_medical_intent
from app.rag.explainer import explain_with_strict_rag
from app.core.limiter import limiter, LIMIT_STRATEGY
from app.whatsapp.sender import send_whatsapp_message
from app.config import WHATSAPP_VERIFY_TOKEN
from app.core.logger import log_clinical_session

router = APIRouter()

DEMOGRAPHIC_QUESTIONS = [
    {"key": "age", "question": "To provide accurate guidance, please provide the patient's *Age*."},
    {"key": "gender", "question": "What is the patient's *Gender*?"},
    {"key": "weight", "question": "What is the patient's *Weight in kg*? (Essential for accurate dosing)."},
    {"key": "comorbidities", "question": "Are there any known *comorbidities* or allergies (e.g., Diabetes, Asthma)?"}
]

@router.get("/webhook-whatsapp")
async def verify(hub_mode: str = Query(None, alias="hub.mode"), 
                 hub_challenge: str = Query(None, alias="hub.challenge"), 
                 hub_verify_token: str = Query(None, alias="hub.verify_token")):
    if hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=403)

@router.post("/webhook-whatsapp")
@limiter.limit(LIMIT_STRATEGY)  # Apply rate limiting to the POST endpoint
async def receive(request: Request, background_tasks: BackgroundTasks):
    """
    Main entry point for incoming WhatsApp messages. This endpoint:
    1. Parses incoming messages and identifies the sender and text.
    2. Uses a turn-level intent classifier to determine if the message is a general query or a clinical case.
    3. If it's a clinical case, initiates a demographic collection sequence.
    4. Once all necessary information is collected, it processes the query with RAG and responds.
    """
    print(LIMIT_STRATEGY)
    payload = await request.json()
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                sender_id = msg.get("from")
                text = msg.get("text", {}).get("body")
                if sender_id and text:
                    background_tasks.add_task(medical_orchestrator, sender_id, text)
    return {"status": "accepted"}

async def medical_orchestrator(sender_id: str, text: str):
    """Orchestrates the entire flow for processing incoming WhatsApp messages, including intent detection, demographic collection, RAG processing, and response sending."""
    try:
        state = get_state(sender_id)
        
        # 1. GLOBAL RESET LOGIC
        if text.lower() in ["/start", "hi", "hello", "restart"]:
            clear_state(sender_id)
            welcome = (
                "🏥 *Clinical Evidence Assistant (v2)*\n\n"
                "Example Usages:\n"
                "• *General:* 'What is the Dose of Amoxicillin?'\n"
                "• *Case:* 'Child with high fever...'\n\n"
                "Type */start* to reset."
            )
            await send_whatsapp_message(sender_id, welcome)
            set_state(sender_id, {"step": "READY", "demographics": {}})
            return

        # 2. TURN-LEVEL INTENT DETECTION
        analysis = await detect_medical_intent(text)
        intent_type = analysis.get("type") # 'general' or 'case'
        expanded_q = analysis.get("expanded_query", text)

        # 3. DEMOGRAPHIC COLLECTION GATE
        # We only enter/stay here if the intent is a 'case'
        if state and state.get("step") == "AWAITING_DEMOGRAPHICS":
            # If user switches to a general query mid-collection, break out
            if intent_type == "general":
                state["step"] = "READY"
                state["pending_query"] = None
                # Fall through to PRIMARY PROCESSING below
            else:
                idx = state.get("demographic_idx", 0)
                key = DEMOGRAPHIC_QUESTIONS[idx]["key"]
                state["demographics"][key] = text
                
                if idx + 1 < len(DEMOGRAPHIC_QUESTIONS):
                    state["demographic_idx"] = idx + 1
                    next_q = DEMOGRAPHIC_QUESTIONS[idx+1]["question"]
                    set_state(sender_id, state)
                    return await send_whatsapp_message(sender_id, next_q)
                else:
                    state["step"] = "READY"
                    query_to_process = state.get("pending_query", text)
                    answer = await explain_with_strict_rag(query_to_process, expanded_q, state["demographics"])
                    
                    log_clinical_session(sender_id, query_to_process, "case", state["demographics"], state.get("last_refs", []), answer)
                    await send_whatsapp_message(sender_id, answer)
                    
                    state.update({"pending_query": None, "demographics": {}})
                    set_state(sender_id, state)
                    return

        # 4. PRIMARY PROCESSING (READY STATE)
        if intent_type == "case":
            # Start demographic sequence for new cases
            set_state(sender_id, {
                "step": "AWAITING_DEMOGRAPHICS",
                "demographic_idx": 0,
                "pending_query": text,
                "demographics": {}
            })
            return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[0]["question"])
        
        else:
            # DIRECT RAG for General Queries (No demographics asked)
            answer = await explain_with_strict_rag(text, expanded_q, {})
            
            log_clinical_session(sender_id, text, "general", {}, state.get("last_refs", []) if state else [], answer)
            await send_whatsapp_message(sender_id, answer)
            
            if not state:
                set_state(sender_id, {"step": "READY", "demographics": {}})

    except Exception as e:
        print(f"Error in orchestrator: {e}")
        await send_whatsapp_message(sender_id, "⚠️ Technical issue. Please try again.")
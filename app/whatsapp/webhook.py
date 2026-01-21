from fastapi import APIRouter, Request, BackgroundTasks, Query, Response
from fastapi.responses import PlainTextResponse
from app.state_store.store import get_state, set_state, clear_state
from app.core.intent_classifier import detect_medical_intent
from app.rag.explainer import explain_with_strict_rag
from app.whatsapp.sender import send_whatsapp_message
from app.config import WHATSAPP_VERIFY_TOKEN

router = APIRouter()

# Sequential Demographic Sequence
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
        return PlainTextResponse(content=hub_challenge)
    return Response(status_code=403)

@router.post("/webhook-whatsapp")
async def receive(request: Request, background_tasks: BackgroundTasks):
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
    state = get_state(sender_id)
    
    # 1. GLOBAL RESET & START LOGIC
    if not state or text.lower() in ["/start", "hi", "hello", "restart"]:
        clear_state(sender_id)
        welcome = (
            "🏥 *Clinical Evidence Assistant (v2)*\n\n"
            "Grounded *strictly* in ICMR-STW official guidelines.\n\n"
            "• *General Queries:* 'Dose of Amoxicillin?'\n"
            "• *Patient Cases:* 'Child with high fever...'\n\n"
            "Type */start* to reset session data at any time."
        )
        await send_whatsapp_message(sender_id, welcome)
        set_state(sender_id, {"step": "READY", "demographics": {}})
        return

    # 2. TURN-LEVEL INTENT DETECTION
    # We analyze intent on every message to handle topic switching or new cases
    analysis = await detect_medical_intent(text)
    intent_type = analysis.get("type")
    expanded_q = analysis.get("expanded_query", text)

    # 3. DEMOGRAPHIC COLLECTION GATE
    if state.get("step") == "AWAITING_DEMOGRAPHICS":
        # Check if user is trying to switch to a general query mid-collection
        if intent_type == "general" and len(text.split()) > 3:
            state["step"] = "READY"
            state["pending_query"] = None
            # Allow flow to fall through to RAG execution below
        else:
            idx = state.get("demographic_idx", 0)
            key = DEMOGRAPHIC_QUESTIONS[idx]["key"]
            state["demographics"][key] = text
            
            # Continue to next question or process case
            if idx + 1 < len(DEMOGRAPHIC_QUESTIONS):
                state["demographic_idx"] = idx + 1
                next_q = DEMOGRAPHIC_QUESTIONS[idx+1]["question"]
                set_state(sender_id, state)
                return await send_whatsapp_message(sender_id, next_q)
            else:
                # Sequence complete -> Execute RAG for the PENDING clinical query
                state["step"] = "READY"
                query_to_process = state.get("pending_query", text)
                
                answer = await explain_with_strict_rag(
                    query=query_to_process, 
                    expanded_search=expanded_q, 
                    demographics=state["demographics"]
                )
                await send_whatsapp_message(sender_id, answer)
                
                # Cleanup state for next query
                state["pending_query"] = None
                state["demographics"] = {} # Clear for next patient
                set_state(sender_id, state)
                return

    # 4. PRIMARY PROCESSING (READY STATE)
    if intent_type == "case":
        # New Clinical Case Detected: Clear old context and start fresh collection
        state.update({
            "step": "AWAITING_DEMOGRAPHICS",
            "demographic_idx": 0,
            "pending_query": text,
            "demographics": {} 
        })
        set_state(sender_id, state)
        return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[0]["question"])
    
    else:
        # General Medical Query (Definitions/Doses): Direct RAG
        answer = await explain_with_strict_rag(
            query=text, 
            expanded_search=expanded_q, 
            demographics={}
        )
        await send_whatsapp_message(sender_id, answer)
        set_state(sender_id, state)
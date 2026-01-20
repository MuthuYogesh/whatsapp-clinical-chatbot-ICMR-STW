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
    if hub_verify_token == "icmr-stw-demo":
        return PlainTextResponse(content=hub_challenge)
    return Response(status_code=403)

@router.post("/webhook-whatsapp")
async def receive(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                sender_id = msg.get("from")
                text = msg.get("text", {}).get("body")
                if sender_id and text:
                    background_tasks.add_task(medical_orchestrator, sender_id, text)
    return {"status": "accepted"}

async def medical_orchestrator(sender_id: str, text: str):
    state = get_state(sender_id)
    
    # 1. Start/Restart Logic
    if not state or text.lower() in ["/start", "hi", "hello", "restart"]:
        clear_state(sender_id)
        welcome = (
            "🏥 *Welcome, I'm Your Clinical Evidence Assistant*\n\n"
            "Grounded *strictly* in ICMR-STW official guidelines.\n\n"
            "Examples of queries you can ask:\n"
            "• *General Queries:* 'What is the dose for Acyclovir?'\n"
            "• *Patient Cases:* Describe symptoms for treatment flows.\n\n"
            "Type */start* to start or reset at any time."
        )
        await send_whatsapp_message(sender_id, welcome)
        set_state(sender_id, {"step": "READY", "demographics": {}})
        return

    # 2. Demographic Collection Gate
    if state.get("step") == "AWAITING_DEMOGRAPHICS":
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
            query_to_process = state.get("pending_query")
            set_state(sender_id, state)
    else:
        query_to_process = text

    # 3. Intent Detection
    analysis = await detect_medical_intent(query_to_process)
    search_query = analysis.get("expanded_query", query_to_process)
    
    # 4. Trigger Collection if Patient Case detected
    if analysis["type"] == "case" and not state.get("demographics"):
        state.update({"step": "AWAITING_DEMOGRAPHICS", "demographic_idx": 0, "pending_query": query_to_process})
        set_state(sender_id, state)
        return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[0]["question"])

    # 5. Strict RAG Execution
    answer = await explain_with_strict_rag(query_to_process, expanded_search=search_query, demographics=state.get("demographics"))
    await send_whatsapp_message(sender_id, answer)
    
    state["pending_query"] = None
    set_state(sender_id, state)
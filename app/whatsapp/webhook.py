import json
from fastapi import APIRouter, Request, BackgroundTasks, Query, Response, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.state_store.store import get_state, set_state, clear_state
from app.core.intent_classifier import detect_medical_intent
from app.rag.explainer import explain_with_strict_rag
from app.whatsapp.sender import send_whatsapp_message
from app.config import WHATSAPP_VERIFY_TOKEN

router = APIRouter()

# --- 1. Rate Limiting Logic ---

def get_whatsapp_sender_sync(request: Request) -> str:
    """
    Retrieves the phone number from the request state.
    Populated by the middleware below.
    """
    # If middleware hasn't set it, fall back to IP (get_remote_address)
    return getattr(request.state, "sender_phone", get_remote_address(request))

limiter = Limiter(key_func=get_whatsapp_sender_sync)

class WhatsAppStateMiddleware(BaseHTTPMiddleware):
    """
    Industry-grade solution to the 'Single Read Body' problem.
    Reads the phone number from JSON and stores it in request.state for the Limiter.
    """
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and "/webhook-whatsapp" in request.url.path:
            # Clone the body to allow double-reading
            body_bytes = await request.body()
            
            # Simple wrapper to reset body for the next handler
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive

            try:
                payload = json.loads(body_bytes)
                # Dive into the WhatsApp JSON structure
                sender = payload['entry'][0]['changes'][0]['value']['messages'][0]['from']
                request.state.sender_phone = str(sender)
            except (KeyError, IndexError, json.JSONDecodeError):
                request.state.sender_phone = get_remote_address(request)
        
        response = await call_next(request)
        return response

# Note: You must add this middleware in app/main.py: 
# app.add_middleware(WhatsAppStateMiddleware)

# --- 2. Constants & Configuration ---

DEMOGRAPHIC_QUESTIONS = [
    {"key": "age", "question": "To provide accurate guidance, please provide the patient's *Age*."},
    {"key": "gender", "question": "What is the patient's *Gender*?"},
    {"key": "weight", "question": "What is the patient's *Weight in kg*? (Essential for accurate dosing)."},
    {"key": "comorbidities", "question": "Are there any known *comorbidities* or allergies (e.g., Diabetes, Asthma)?"}
]

# --- 3. Endpoint Handlers ---

@router.get("/webhook-whatsapp")
async def verify(hub_mode: str = Query(None, alias="hub.mode"), 
                 hub_challenge: str = Query(None, alias="hub.challenge"), 
                 hub_verify_token: str = Query(None, alias="hub.verify_token")):
    if hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    return Response(status_code=403)


@router.post("/webhook-whatsapp")
@limiter.limit("10/minute") # Setting to 2/min per phone number
async def receive(request: Request, background_tasks: BackgroundTasks):
    """
    Main Entry Point for whatsapp messages. Rate Limited by Phone Number.
    """
    # Body is already available thanks to middleware
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

# --- 4. Clinical Orchestration Logic ---

async def medical_orchestrator(sender_id: str, text: str):
    try:
        state = get_state(sender_id)
        
        # 1. GLOBAL RESET & START LOGIC
        if not state or text.lower() in ["/start", "hi", "hello", "restart"]:
            clear_state(sender_id)
            welcome = (
                "🏥 *Clinical Evidence Assistant (v2)*\n\n"
                "Grounded *strictly* in ICMR-STW official guidelines.\n\n"
                "Example Usages:\n"
                "• *General Queries:* 'eg: What is the Dose of Amoxicillin?'\n"
                "• *Patient Cases:* 'eg: Child with high fever...'\n\n"
                "Type */start* to reset session data at any time."
            )
            await send_whatsapp_message(sender_id, welcome)
            set_state(sender_id, {"step": "READY", "demographics": {}})
            return

        # 2. TURN-LEVEL INTENT DETECTION
        analysis = await detect_medical_intent(text)
        intent_type = analysis.get("type")
        expanded_q = analysis.get("expanded_query", text)

        # 3. DEMOGRAPHIC COLLECTION GATE
        if state.get("step") == "AWAITING_DEMOGRAPHICS":
            # Check if user is trying to switch to a general query mid-collection
            if intent_type == "general" and len(text.split()) > 3:
                state["step"] = "READY"
                state["pending_query"] = None
                # Allow flow to fall through to primary processing
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
                    
                    answer = await explain_with_strict_rag(
                        query=query_to_process, 
                        expanded_search=expanded_q, 
                        demographics=state["demographics"]
                    )
                    await send_whatsapp_message(sender_id, answer)
                    
                    state["pending_query"] = None
                    state["demographics"] = {}
                    set_state(sender_id, state)
                    return

        # 4. PRIMARY PROCESSING (READY STATE)
        if intent_type == "case":
            state.update({
                "step": "AWAITING_DEMOGRAPHICS",
                "demographic_idx": 0,
                "pending_query": text,
                "demographics": {} 
            })
            set_state(sender_id, state)
            return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[0]["question"])
        
        else:
            answer = await explain_with_strict_rag(
                query=text, 
                expanded_search=expanded_q, 
                demographics={}
            )
            await send_whatsapp_message(sender_id, answer)
            set_state(sender_id, state)
    
    except Exception as e:
        print(f"Error in medical_orchestrator for sender {sender_id}: {str(e)}")
        
        error_msg = (
            "⚠️ *Technical Connectivity Issue*\n\n"
            "I'm having trouble reaching the clinical database right now. "
            "Please try again in a few minutes."
        )
        
        await send_whatsapp_message(sender_id, error_msg)
        clear_state(sender_id)
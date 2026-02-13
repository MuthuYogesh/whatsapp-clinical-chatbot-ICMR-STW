import json
from fastapi import APIRouter, Request, BackgroundTasks, Query, Response
from app.state_store.store import get_state, set_state, clear_state
from app.core.intent_classifier import detect_medical_intent
from app.rag.explainer import explain_with_strict_rag, explain_with_hybrid_rag
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

SELECTION_MENU = (
    "\n\n---\n"
    "🔄 *Select next action:*\n"
    "*1* ➔ New Patient Case\n"
    "*2* ➔ New General Search\n"
    "Type */start* to reset."
)

@router.get("/webhook-whatsapp")
async def verify(hub_mode: str = Query(None, alias="hub.mode"), 
                 hub_challenge: str = Query(None, alias="hub.challenge"), 
                 hub_verify_token: str = Query(None, alias="hub.verify_token")):
    if hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=403)

@router.post("/webhook-whatsapp")
@limiter.limit(LIMIT_STRATEGY)
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
    try:
        state = get_state(sender_id) or {"step": "READY"}
        
        # 1. GLOBAL RESET
        if text.lower() in ["/start", "hi", "hello", "restart"]:
            clear_state(sender_id)
            welcome = (
                "🏥 *Clinical Evidence Assistant (v4)*\n\n"
                "Please select your pathway:\n"
                "*1* ➔ *Patient Case* (Strict ICMR Standard Treatment Workflows (STW) Guidelines)\n"
                "*2* ➔ *General Search* (Hybrid Knowledge)\n\n"
                "Reply with *1* or *2* to begin."
            )
            await send_whatsapp_message(sender_id, welcome)
            set_state(sender_id, {"step": "SELECT_PATHWAY"})
            return

        # 2. PATHWAY SELECTION
        if state.get("step") == "SELECT_PATHWAY":
            if text == "1":
                state.update({"step": "AWAITING_CASE_QUERY", "pathway": "case"})
                set_state(sender_id, state)
                return await send_whatsapp_message(sender_id, "📝 Describe the *Patient Case* (e.g., 'Child with high fever').")
            elif text == "2":
                state.update({"step": "AWAITING_SEARCH_QUERY", "pathway": "search"})
                set_state(sender_id, state)
                return await send_whatsapp_message(sender_id, "🔍 What would you like to *Search*?")
            else:
                return await send_whatsapp_message(sender_id, "⚠️ Please reply with *1* or *2*.")

        # 3. CASE PATHWAY
        if state.get("step") == "AWAITING_CASE_QUERY":
            state.update({"step": "AWAITING_DEMOGRAPHICS", "pending_query": text, "demographic_idx": 0, "demographics": {}})
            set_state(sender_id, state)
            return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[0]["question"])

        if state.get("step") == "AWAITING_DEMOGRAPHICS":
            idx = state.get("demographic_idx", 0)
            key = DEMOGRAPHIC_QUESTIONS[idx]["key"]
            state["demographics"][key] = text
            
            if idx + 1 < len(DEMOGRAPHIC_QUESTIONS):
                state["demographic_idx"] = idx + 1
                set_state(sender_id, state)
                return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[idx+1]["question"])
            else:
                # --- PROCESS CASE ---
                analysis = await detect_medical_intent(state["pending_query"])
                answer = await explain_with_strict_rag(
                    query=state["pending_query"], 
                    expanded_search=analysis.get("expanded_query"), 
                    demographics=state["demographics"],
                    intent_data=analysis
                )
                
                # Append the menu and loop back the state
                final_response = answer + SELECTION_MENU
                await send_whatsapp_message(sender_id, final_response)
                log_clinical_session(sender_id, state["pending_query"], "case", state["demographics"], [], answer)
                
                set_state(sender_id, {"step": "SELECT_PATHWAY"})
                return

        # 4. SEARCH PATHWAY
        if state.get("step") == "AWAITING_SEARCH_QUERY":
            analysis = await detect_medical_intent(text)
            answer = await explain_with_hybrid_rag(
                query=text,
                expanded_search=analysis.get("expanded_query")
            )
            
            # Append the menu and loop back the state
            final_response = answer + SELECTION_MENU
            await send_whatsapp_message(sender_id, final_response)
            log_clinical_session(sender_id, text, "search", {}, [], answer)
            
            set_state(sender_id, {"step": "SELECT_PATHWAY"})
            return

    except Exception as e:
        print(f"Error in v5 Orchestrator: {e}")
        await send_whatsapp_message(sender_id, "⚠️ Technical issue. Type */start* to reset.")
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
        state = get_state(sender_id) or {"step": "READY", "demographics": {}}
        
        # 1. GLOBAL RESET
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

        # 2. FLOW ROUTING
        # IF WE ARE COLLECTING DATA:
        if state.get("step") == "AWAITING_DEMOGRAPHICS":
            idx = state.get("demographic_idx", 0)
            key = DEMOGRAPHIC_QUESTIONS[idx]["key"]
            
            # Save current answer
            state["demographics"][key] = text
            
            if idx + 1 < len(DEMOGRAPHIC_QUESTIONS):
                # Ask Next Question
                state["demographic_idx"] = idx + 1
                next_q = DEMOGRAPHIC_QUESTIONS[idx+1]["question"]
                set_state(sender_id, state)
                return await send_whatsapp_message(sender_id, next_q)
            else:
                # --- CASE COMPLETE: PROCESS FINAL RAG ---
                # Retrieve the locked data
                original_query = state.get("pending_query")
                original_analysis = state.get("pending_analysis", {})
                
                # IMPORTANT: Use the original intent data for the explainer
                answer = await explain_with_strict_rag(
                    query=original_query, 
                    expanded_search=original_analysis.get("expanded_query"), 
                    demographics=state["demographics"],
                    intent_data=original_analysis
                )
                
                await send_whatsapp_message(sender_id, answer)
                log_clinical_session(sender_id, original_query, "case", state["demographics"], [], answer)
                
                # Clean up state
                clear_state(sender_id)
                set_state(sender_id, {"step": "READY", "demographics": {}})
                return

        # 3. NEW INTENT DETECTION (Only reached if not in the middle of a case)
        analysis = await detect_medical_intent(text)
        intent_type = analysis.get("type") 
        expanded_q = analysis.get("expanded_query", text)

        # 4. PRIMARY PROCESSING (READY STATE)
        if intent_type == "case":
            # Initiate demographic sequence
            set_state(sender_id, {
                "step": "AWAITING_DEMOGRAPHICS",
                "demographic_idx": 0,
                "pending_query": text,
                "pending_analysis": analysis, # Save the clinical domains/intent here!
                "demographics": {}
            })
            return await send_whatsapp_message(sender_id, DEMOGRAPHIC_QUESTIONS[0]["question"])
        
        else:
            # General Queries
            answer = await explain_with_strict_rag(
                query=text, 
                expanded_search=expanded_q, 
                demographics={}, 
                intent_data=analysis
            )
            await send_whatsapp_message(sender_id, answer)
            log_clinical_session(sender_id, text, "general", {}, [], answer)
            set_state(sender_id, {"step": "READY", "demographics": {}})

    except Exception as e:
        print(f"Error in orchestrator: {e}")
        await send_whatsapp_message(sender_id, "⚠️ Technical issue. Please try again.")
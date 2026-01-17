from fastapi import APIRouter, Request, BackgroundTasks, Query, Response
from fastapi.responses import PlainTextResponse
from app.models.normalized_messages import NormalizedMessage
from app.state_store.store import clear_state, get_state, set_state
from app.core.fallback import fallback_response
from app.core.intent_classifier import detect_intent
from app.core.stw_selector import select_stw_candidates
from app.core.stw_readiness import check_stw_readiness
from app.core.clarification_generator import generate_clarification_questions
from app.core.fact_extractor import extract_clinical_facts
from app.core.rule_engine.dispatcher import apply_stw_rules
from app.rag.explainer import explain_with_rag
from app.whatsapp.sender import send_whatsapp_message
from app.config import WHATSAPP_VERIFY_TOKEN

router = APIRouter()

MAX_CLARIFICATION_ATTEMPTS = 3

def data_normalizer(payload: dict) -> NormalizedMessage:
    """Extracts content while satisfying all Pydantic model requirements."""
    return NormalizedMessage(
        channel="whatsapp",
        sender_id=payload.get("from"),
        sender_name="Doctor",
        message_id=payload.get("id"),
        timestamp=int(payload.get("timestamp") or 0),
        message_type=payload.get("type", "text"),
        content=payload.get("text", {}).get("body"),
        raw_payload=payload,
    )

def render_questions(questions: dict) -> str:
    """Renders a list of questions into a WhatsApp-friendly string."""
    return "\n".join(q["question"] if isinstance(q, dict) else str(q) for q in questions.get("questions", []))

# =========================================================
# MANDATORY META HANDSHAKE (GET)
# =========================================================
@router.get("/webhook-whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == "icmr-stw-demo":
        return PlainTextResponse(content=hub_challenge)
    return Response(content="Verification failed", status_code=403)

# =========================================================
# WEBHOOK RECEIVER (POST)
# =========================================================
@router.post("/webhook-whatsapp")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """Receives incoming WhatsApp messages and offloads to background processing."""
    payload = await request.json()
    if payload.get("object") != "whatsapp_business_account":
        return {"status": "ignored"}

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                sender_id = message.get("from")
                text = message.get("text", {}).get("body")
                if sender_id and text:
                    background_tasks.add_task(handle_clinical_workflow, sender_id, text, message)

    return {"status": "accepted"}

# =========================================================
# CLINICAL WORKFLOW ORCHESTRATOR
# =========================================================
async def handle_clinical_workflow(sender_id: str, text: str, raw_message: dict):
    """Main state machine for clinical triage and guidance with two-step confirmation."""
    state = get_state(sender_id)
    normalized = data_normalizer(raw_message)
    
    # 🔄 GLOBAL RESET: If user says "Hi", "Hello", or "Restart", clear session loops
    if text.lower() in ["hi", "hello", "restart"]:
        clear_state(sender_id)
        await send_whatsapp_message(sender_id, "Hello. I am a clinical assistant designed for ICMR Standard Treatment Workflows. Please describe a patient's symptoms or ask a clinical question to begin.")
        return

    # STEP 1: Initial Analysis & Interactive Confirmation Request
    if state is None:
        # Detect Intent (Search vs. Case) and Identify STW Candidates
        intent = await detect_intent(normalized)

        case = ["CASE", "SEARCH"]
        menu = f"I've analyzed your message. Please confirm the following to proceed:\n\n"
        menu += f"📚 *Intents:*\n"
        for i, r in enumerate(case, 1):
            menu += f"{i}️⃣ *{r}*\n"
        
        menu += "\n👉 *Select the correct Intent to start the workflow.*"

        set_state(sender_id, {
            "stage": "AWAITING_CONFIRMATION_STW",
            "intent": intent,
            "rankings": None,
            "original_text": text
        })
        await send_whatsapp_message(sender_id, menu)
        return


    elif state.get("stage") == "AWAITING_CONFIRMATION_STW":
        selection_result = await select_stw_candidates(normalized)
        rankings = selection_result.get("rankings", [])

        if not rankings:
            await send_whatsapp_message(sender_id, "No matching ICMR guidelines found. Please provide more clinical details.")
            return
        try:
            choice_idx = int(text.strip())
            if choice_idx == 1:
                intent = "CASE"
            elif choice_idx == 2:
                intent = "SEARCH"
            else:
                await send_whatsapp_message(sender_id, "❌ Invalid selection. Please reply with '1' for CASE or '2' for SEARCH.")
                return
        except ValueError:
            await send_whatsapp_message(sender_id, "❌ Please reply with '1' for CASE or '2' for SEARCH to choose the intent.")
            return
        # Prepare the Two-Step Interactive Confirmation Message
        menu = f"I've analyzed your message. Please confirm the following to proceed:\n\n"
        menu += f"📍 *Intent Identified:* {'PATIENT CASE' if intent == 'CASE' else 'GENERAL SEARCH'}\n\n"
        menu += f"📚 *Probable ICMR Guidelines:*\n"
        for i, r in enumerate(rankings, 1):
            name = r['stw'].replace('_', ' ')
            menu += f"{i}️⃣ *{name}* ({int(r['weight']*100)}%)\n"
        
        menu += "\n👉 *Select the correct guideline number to start the workflow.*"
        
        # Save state for Stage 1 confirmation
        set_state(sender_id, {
            "stage": "AWAITING_CONFIRMATION",
            "intent": intent,
            "rankings": rankings,
            "original_text": get_state(sender_id)["original_text"]
        })
        await send_whatsapp_message(sender_id, menu)
        return

    # STEP 2: Process User Confirmation and Trigger Appropriate Engine
    elif state.get("stage") == "AWAITING_CONFIRMATION":
        try:
            choice_idx = int(text.strip()) - 1
            if 0 <= choice_idx < len(state["rankings"]):
                selected_stw = state["rankings"][choice_idx]["stw"]
                intent = state["intent"]
                original_text = state["original_text"]

                # PATH A: PATIENT CASE (Rule Engine + RAG + LLM)
                if intent == "CASE":
                    await start_fact_extraction_workflow(sender_id, selected_stw, original_text)
                
                # PATH B: GENERAL SEARCH (RAG + LLM only)
                else:
                    explanation = await explain_with_rag(selected_stw, {}, {}, query_override=original_text)
                    await send_whatsapp_message(sender_id, f"📚 *Clinical Information:* {selected_stw.replace('_', ' ')}\n\n{explanation}")
                    clear_state(sender_id) # Task complete for search
            else:
                await send_whatsapp_message(sender_id, "❌ Invalid selection. Please reply with one of the numbers listed above.")
        except ValueError:
            await send_whatsapp_message(sender_id, "❌ Please reply with a number (e.g., '1') to choose the guideline.")

    # STAGE 3: Handle Guideline Clarifications (For Cases Only)
    elif state.get("stage") == "AWAITING_CLARIFICATION":
        state["clarification_attempts"] = state.get("clarification_attempts", 0) + 1
        if state["clarification_attempts"] > MAX_CLARIFICATION_ATTEMPTS:
            await send_whatsapp_message(sender_id, fallback_response("unclear_reply"))
            clear_state(sender_id)
            return

        # Merge new replies into existing clinical facts
        new_facts = await extract_clinical_facts(state["stw"], text)
        for k, v in new_facts.items():
            if v is not None: 
                state["clinical_facts"][k] = v

        # Re-check readiness (handles emergency bypasses based on ICMR criteria)
        readiness = check_stw_readiness(state["stw"], state["clinical_facts"])
        if readiness["ready"]:
            await execute_final_guidance(sender_id, state["stw"], state["clinical_facts"])
        else:
            questions = await generate_clarification_questions(state["stw"], readiness["missing_information"])
            await send_whatsapp_message(sender_id, render_questions(questions))
            set_state(sender_id, state)

async def start_fact_extraction_workflow(sender_id, stw_name, input_text):
    """Orchestrates fact extraction and readiness check for a confirmed Case."""
    current_facts = await extract_clinical_facts(stw_name, input_text)
    
    # Readiness check triggers immediate bypass for critical markers like GCS < 8
    readiness = check_stw_readiness(stw_name, current_facts)
    
    if readiness["ready"]:
        await execute_final_guidance(sender_id, stw_name, current_facts)
    else:
        set_state(sender_id, {
            "stage": "AWAITING_CLARIFICATION", 
            "stw": stw_name, 
            "clinical_facts": current_facts, 
            "clarification_attempts": 0
        })
        questions = await generate_clarification_questions(stw_name, readiness["missing_information"])
        await send_whatsapp_message(sender_id, render_questions(questions))

async def execute_final_guidance(sender_id, stw_name, facts):
    """Applies rule engine and provides referenced clinical evidence via RAG + LLM."""
    # Applies deterministic rules (e.g., PICU referral for GCS < 8)
    result = apply_stw_rules(stw_name, facts)
    # Generates clinical evidence/reasoning using RAG + LLM
    explanation = await explain_with_rag(stw_name, result, facts)
    
    plan_text = "\n".join([f"• {p}" for p in result.get("plan", [])])
    final_msg = f"*{result['message']}*\n\n*MANAGEMENT PLAN:*\n{plan_text}\n\n*EVIDENCE:*\n{explanation}"
    
    await send_whatsapp_message(sender_id, final_msg.strip())
    clear_state(sender_id)
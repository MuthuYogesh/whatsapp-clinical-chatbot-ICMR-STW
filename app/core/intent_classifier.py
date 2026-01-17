import re
from app.llm.groq_client import call_groq
from app.models.normalized_messages import NormalizedMessage

async def detect_intent(payload: NormalizedMessage) -> str:

    if not payload.content:
        return "unknown"

    text = payload.content.lower().strip()
    
      # 1. FAST GREETING CHECK
    greet_set = {"hi", "hello", "hey", "good morning", "good evening", "morning", "evening"}
    clean_str = re.sub(r'[^\w\s]', ' ', text)
    msg_set = set(clean_str.split())
    
    if any(greet_word in msg_set for greet_word in greet_set):
        # If it's just a short greeting, return "greet"
        if len(msg_set) <= 2:
            return "greet"

    # 2. EXPANDED CLINICAL KEYWORDS (Safety Net)
    # Includes clinical markers like GCS and symptoms from ICMR STWs [cite: 10, 11]
    clinical_keywords = {
        "mg", "ml", "tablet", "antibiotic", "dose", "days", "patient",
        "fever", "seizure", "convulsion", "drowsy", "unconscious", "gcs", 
        "nasal", "sinus", "blocked", "discharge", "pain", "breathing",
        "vitals", "bp", "pulse", "stiffness", "lethargy", "vomiting", "headache", "unconscious", "altered sensorium", "immuno", "diabetic", "sinus"
    }
    
    if any(word in msg_set for word in clinical_keywords):
        return "clinical"

    # 3. LLM CLASSIFICATION (Generative Logic)
    # Using the centralized client with 'text' response format
    prompt = f"""
    Classify the intent of this doctor's message.
    Message: "{payload.content}"
    
    Return ONLY one word:
    - "clinical": If describing symptoms, patient data, vitals, or medical queries.
    - "greet": If it is just a greeting.
    - "unknown": If it is social chatter, "ok", "thanks", or irrelevant.
    """
    
    llm_response = await call_groq(
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
        response_format="text"
    )

    if llm_response:
        # Clean response and validate against expected intents
        intent = re.sub(r'[^\w]', '', llm_response.lower())
        if intent in ["clinical", "greet", "unknown"]:
            return intent

    return "unknown"
from app.llm.groq_client import call_groq

# =========================================================
# DETERMINISTIC FALLBACK QUESTIONS (Safety Net)
# =========================================================
FALLBACK_QUESTIONS = {
    "symptom duration (days)": "How many days have the symptoms been present?",
    "type of nasal discharge": "Is the nasal discharge watery or thick/purulent?",
    "presence of red flags": (
        "Are there any red flag symptoms such as eye swelling, vision problems, "
        "severe headache, or high fever?"
    ),
    "patient's diabetic or immunocompromised status": "Is the patient known to be diabetic or immunocompromised?",
    "Glasgow Coma Scale (GCS) score": "What is the patient's current GCS score?",
    "status of consciousness or seizures": "Please clarify if there is altered sensorium or new-onset seizures.",
    "duration of fever": "How many days has the fever been present?"
}

async def generate_clarification_questions(stw_name: str, missing_information: list[str]) -> dict:
    """
    Generates professional clarification questions using the centralized Groq utility.
    """
    if not missing_information:
        return {"questions": []}

    prompt = f"""
    You are a professional clinical assistant.
    
    TASK:
    Generate short, clear clarification questions for a doctor to gather missing 
    information required for the following STW.
    
    STW: {stw_name}
    Missing Information: {missing_information}
    
    Rules:
    - Ask ONE professional question per missing item.
    - Focus on clinical data points (e.g., "Duration of symptoms" or "GCS score").
    - Do NOT diagnose or give advice.
    - Return STRICT JSON only.
    """

    # Use the centralized utility with json_object format
    data = await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0,
        response_format="json_object"
    )

    # Safety fallback if LLM fails or returns empty/malformed data
    if not data or not data.get("questions"):
        questions_list = []
        for m in missing_information:
            if m in FALLBACK_QUESTIONS:
                questions_list.append({"field": m, "question": FALLBACK_QUESTIONS[m]})
            else:
                questions_list.append({"field": m, "question": f"Please provide details regarding: {m}"})
        return {"questions": questions_list}

    return data
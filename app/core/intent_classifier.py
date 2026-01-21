from app.llm.groq_client import call_groq

async def detect_medical_intent(text: str) -> dict:
    """
    Classifies intent and maps specific drugs to clinical categories 
    to ensure the vector search finds relevant guideline sections.
    """
    prompt = f"""
    Analyze the medical query: "{text}"
    
    TASK:
    1. Classify Type: 
       - "case": Active symptoms, treatment failure, or patient-specific scenarios.
       - "general": Theoretical questions, drug definitions, or general protocols.
       - "greet": Basic greetings.
    2. Search Expansion: 
       - If a specific drug is mentioned, include its therapeutic category (e.g., 'Oxymetazoline' -> 'topical nasal decongestant', 'Amoxicillin' -> 'penicillin antibiotic').
       - If a timeline is mentioned (e.g., '10 days'), include 'treatment failure' or 'referral criteria'.

    Return ONLY JSON:
    {{
        "type": "case" | "general" | "greet",
        "expanded_query": "original term + clinical category + synonyms"
    }}
    """
    
    response = await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        response_format="json_object"
    )
    
    if not response:
        return {"type": "unknown", "expanded_query": text}
        
    return response
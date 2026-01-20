from app.llm.groq_client import call_groq

async def detect_medical_intent(text: str) -> dict:
    """
    Classifies intent and expands the query with clinical synonyms 
    to improve vector search accuracy in ICMR guidelines.
    """
    prompt = f"""
    Analyze the following medical query: "{text}"
    
    TASK:
    1. Classify Type: 
       - "case": Describing symptoms, signs, or a specific patient scenario.
       - "general": Theoretical questions, drug definitions, or general protocols.
       - "greet": Simple greetings or non-medical chat.
    2. Search Expansion: Generate an 'expanded_query' optimized for vector retrieval.
       - If a specific drug is mentioned, include its therapeutic class (e.g., 'Oxymetazoline' -> 'topical nasal decongestant').
       - If a timeline is mentioned (e.g., '10 days'), include terms like 'persistent symptoms', 'treatment failure', or 'duration of therapy'.
       - Use clinical terminology used in standard guidelines.

    Return ONLY a JSON object:
    {{
        "type": "case" | "general" | "greet",
        "expanded_query": "string optimized for clinical document search"
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
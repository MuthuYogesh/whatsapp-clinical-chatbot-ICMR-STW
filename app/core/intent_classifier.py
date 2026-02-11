from app.llm.groq_client import call_groq

async def detect_medical_intent(text: str) -> dict:
    prompt = f"""
    Analyze the medical query: "{text}"
    
    TASK:
    1. Identify Clinical Domain(s): (e.g., ENT, Nephrology, Pediatrics, Pulmonology).
    2. Ranked Differential Mapping: 
       - List the 3 most probable ICMR-STW clinical conditions in order of probability.
       - Example: "Sinus pain" -> 1. Acute Rhinosinusitis (ENT), 2. Allergic Rhinitis (ENT), 3. Common Cold (Pulm/Gen).
    3. Category Expansion: Add formal terms like 'Management Protocol' or 'Drug Dosage'.

    Return ONLY JSON:
    {{
        "type": "case" | "general",
        "domains": ["Domain1", "Domain2"],
        "ranked_conditions": [
            {{"name": "Condition 1", "probability": "High"}},
            {{"name": "Condition 2", "probability": "Medium"}}
        ],
        "expanded_query": "concatenated search terms for vector DB"
    }}
    """
    response = await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        response_format="json_object"
    )
    return response if response else {{"type": "unknown", "expanded_query": text}}
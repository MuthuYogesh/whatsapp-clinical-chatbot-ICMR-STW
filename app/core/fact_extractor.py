import json
from app.llm.groq_client import call_groq

FACT_SCHEMAS = {
    "ENT_Acute_Rhinosinusitis": {
        "duration_days": None,
        "nasal_discharge_type": None, 
        "is_diabetic_immuno": None,       
        "red_flags_present": None,
        "antibiotic_non_resolution_10_days": None 
    },
    "PEDS_Acute_Encephalitis_Syndrome": {
        "fever_days": None,
        "altered_sensorium": None,
        "seizures_present": None,
        "gcs_score": None,               
        "respiratory_distress": None,    
        "refractory_seizures": None,     
        "danger_signs_present": None     
    }
}

async def extract_clinical_facts(stw_name: str, user_reply: str) -> dict:
    if stw_name not in FACT_SCHEMAS:
        raise ValueError(f"Unsupported STW: {stw_name}")

    schema = FACT_SCHEMAS[stw_name]
    if not user_reply:
        return schema.copy()

    prompt = f"""
        You are a medical data extractor for the ICMR STW: {stw_name}.
        TASK: Extract facts from the message: "{user_reply}"
        Return ONLY JSON matching this schema: {json.dumps(schema)}
        
        RULES:
        1. Booleans: Set to `false` if the user denies a condition (e.g., "Not diabetic", "No seizures").
        2. Emergency Synonyms: 
           - "Comatose", "Unconscious", "Drowsy", "Passed out" -> 'altered_sensorium': true.
           - "Diabetes", "DM", "Sugar history" -> 'is_diabetic_immuno': true.
        3. Numbers: Extract integers for 'duration_days', 'fever_days', and 'gcs_score'.
        4. Normalization: Map 'watery/clear' to 'watery' and 'thick/pus/yellow' to 'purulent'.
    """
    
    data = await call_groq(messages=[{"role": "user", "content": prompt}], response_format="json_object")
    
    if data is None:
        return schema.copy()

    return {k: data.get(k) for k in schema}
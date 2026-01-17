import json
from app.llm.groq_client import call_groq

FACT_SCHEMAS = {
    "PEDS_Acute_Encephalitis_Syndrome": {
        "fever_present": None,
        "fever_days": None,
        "altered_sensorium": None,   # unconscious/drowsy
        "seizures_present": None,
        "gcs_score": None,           # Examination: GCS
        "shock_present": None,       # Examination: BP/Pulse
        "abnormal_posturing": None,  # Examination: Posturing
        "abnormal_breathing": None,  # Examination: Breathing
        "refractory_seizures": None
    },
    "ENT_Acute_Rhinosinusitis": {
        "duration_days": None,
        "nasal_discharge_present": None,
        "nasal_discharge_type": None,
        "facial_pain_present": None,
        "is_diabetic_immuno": None,       
        "red_flags_present": None,
        "antibiotic_failure_10_days": None 
    }
}

async def extract_clinical_facts(stw_name: str, user_reply: str) -> dict:
    schema = FACT_SCHEMAS.get(stw_name, {})
    prompt = f"""
        Extract facts for {stw_name} from: "{user_reply}"
        Return JSON ONLY: {json.dumps(schema)}
        RULES: 
        1. 'altered_sensorium': true if unconscious/coma/drowsy.
        2. 'fever_present': true if fever/103F mentioned.
        3. Numbers like GCS must be integers.
    """
    data = await call_groq(messages=[{"role": "user", "content": prompt}], response_format="json_object")
    return {k: data.get(k) if data else None for k in schema}
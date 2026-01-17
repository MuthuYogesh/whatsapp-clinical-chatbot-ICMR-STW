from typing import Dict
from app.llm.groq_client import call_groq
from app.models.normalized_messages import NormalizedMessage

ALLOWED_STWS = ["ENT_Acute_Rhinosinusitis", "PEDS_Acute_Encephalitis_Syndrome"]

async def select_stw_candidates(payload: NormalizedMessage) -> Dict:
    """Identifies and ranks potential ICMR guidelines. Adds CLARIFY intent for ambiguity."""
    prompt = f"""
        Analyze medical query: "{payload.content}"
        
        TASK:
        1. Intent: 
           - 'SEARCH' (general question, e.g., "What is AES?", "Doses for Ceftriaxone?")
           - 'CASE' (patient symptoms or test results, e.g., "Child is unconscious")
           - 'CLARIFY' (ambiguous or one-word queries)
        2. Rank Guidelines: PEDS_Acute_Encephalitis_Syndrome, ENT_Acute_Rhinosinusitis.

        Return ONLY JSON:
        {{
            "intent": "CASE" | "SEARCH" | "CLARIFY",
            "rankings": [
                {{ "stw": "STW_NAME", "weight": float, "reason": "clinical justification" }}
            ]
        }}
    """
    response = await call_groq(messages=[{"role": "user", "content": prompt}], response_format="json_object")
    rankings = [r for r in response.get("rankings", []) if r["stw"] in ALLOWED_STWS]
    rankings.sort(key=lambda x: x["weight"], reverse=True)

    return {"intent": response.get("intent", "CASE"), "rankings": rankings}
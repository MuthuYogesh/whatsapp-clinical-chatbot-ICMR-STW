from typing import Dict
from app.llm.groq_client import call_groq
from app.models.normalized_messages import NormalizedMessage

ALLOWED_STWS = ["ENT_Acute_Rhinosinusitis", "PEDS_Acute_Encephalitis_Syndrome"]

async def select_stw_candidates(payload: NormalizedMessage) -> Dict:
    """Identifies and ranks potential ICMR guidelines by relevance and severity."""
    if not payload.content:
        return {"rankings": [], "intent": "CASE"}

    prompt = f"""
        Analyze medical symptoms: "{payload.content}"
        
        TASK: Rank potential ICMR STWs by clinical relevance.
        
        GUIDELINES:
        - PEDS_Acute_Encephalitis_Syndrome: Suspicion if CHILD has Fever + (Unconscious OR Seizures).
        - ENT_Acute_Rhinosinusitis: Nasal discharge, sinus pain, facial pressure.

        WEIGHTING RULES:
        1. Neuro symptoms (Unconscious, Seizures) in children = HIGH priority (Weight 0.9-1.0).
        2. ENT symptoms = MEDIUM priority (Weight 0.3-0.5) unless neuro symptoms are present.
        3. Omit only if 100% irrelevant.

        Return ONLY JSON: 
        {{
            "intent": "CASE" | "SEARCH",
            "rankings": [
                {{ "stw": "STW_NAME", "weight": float, "reason": "short clinical justification" }}
            ]
        }}
    """

    response_data = await call_groq(messages=[{"role": "user", "content": prompt}], response_format="json_object")
    
    # Filter and sort by clinical weight
    rankings = [r for r in response_data.get("rankings", []) if r["stw"] in ALLOWED_STWS]
    rankings.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "intent": response_data.get("intent", "CASE"),
        "rankings": rankings
    }
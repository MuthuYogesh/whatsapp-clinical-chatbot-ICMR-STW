import json
import os
from datetime import datetime
from typing import Any, Dict, List

# log file path for clinical interactions. Each line is a JSON object with details of the session, including demographics, retrieved sources, and AI response.
LOG_FILE = "logs/clinical_audit.jsonl"

def log_clinical_session(
    sender_id: str, 
    user_query: str, 
    intent: str, 
    demographics: Dict[str, Any], 
    retrieved_refs: List[str], 
    ai_response: str
):
    """
    Records a complete clinical interaction for audit and accuracy review.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "doctor_id": sender_id,
        "input": {
            "raw_query": user_query,
            "detected_intent": intent,
            "patient_context": demographics
        },
        "retrieval_metadata": {
            "sources": retrieved_refs,  # List of PDF page/section IDs
            "source_count": len(retrieved_refs)
        },
        "output": ai_response
    }

    # Append as a single line to the JSONL file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
def fallback_response(reason: str) -> str:
    """
    Centralized fallback responses for doctor-facing clinical assistant.
    Provides actionable feedback while strictly avoiding medical advice.
    """

    FALLBACK_MESSAGES = {
        "no_stw_match": (
            "I am unable to match these symptoms to our current ICMR Standard Treatment Workflows "
            "(ENT Acute Rhinosinusitis or PEDS Acute Encephalitis Syndrome). "
            "Please provide more specific clinical details to help me identify the correct guideline."
        ),

        "multiple_stw_overlap": (
            "The symptoms provided overlap with multiple clinical guidelines (e.g., both neurological and respiratory). "
            "Please clarify the primary clinical concern so I can guide you to the correct workflow."
        ),

        "unclear_reply": (
            "I could not clearly understand your last message. "
            "To proceed safely, please rephrase or provide specific clinical markers (e.g., duration, GCS score, or discharge type)."
        ),

        "extraction_failed": (
            "I was unable to extract the required clinical details from your reply. "
            "Please ensure you provide specific values, such as '3 days', 'GCS 10', or 'purulent discharge'."
        ),

        "rule_engine_error": (
            "A technical error occurred while applying the deterministic clinical rules. "
            "Please verify the inputs or restart the clinical assessment."
        ),

        "out_of_scope": (
            "Hi, I am designed to assist specifically with clinical queries based on ICMR STWs. "
            "Please describe a patient's symptoms or clinical signs to begin the management plan."
        )
    }

    return FALLBACK_MESSAGES.get(
        reason,
        "I’m unable to proceed safely with the available information. Please restart the query with more clinical details."
    )
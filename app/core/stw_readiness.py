def check_stw_readiness(stw_name: str, clinical_facts: dict) -> dict:
    """
    Assistant mode: Checks for mandatory data and triggers immediate emergency bypasses.
    """
    if stw_name == "PEDS_Acute_Encephalitis_Syndrome":
        gcs = clinical_facts.get("gcs_score")
        sensorium = clinical_facts.get("altered_sensorium")
        seizures = clinical_facts.get("seizures_present")

        # 🚨 EMERGENCY BYPASS: If unconscious or GCS < 8, proceed to referral logic immediately.
        if sensorium is True or (gcs is not None and gcs < 8):
            return {"ready": True, "is_emergency": True, "missing_information": []}

        # Standard Clinical Suspicion Check
        missing = []
        if clinical_facts.get("fever_days") is None:
            missing.append("duration of fever")
        
        if sensorium is None and seizures is None:
            missing.append("neurological status (seizures/sensorium)")

        return {
            "ready": len(missing) == 0,
            "is_emergency": False,
            "missing_information": missing
        }

    elif stw_name == "ENT_Acute_Rhinosinusitis":
        # EMERGENCY BYPASS: Diabetic status is high risk for Invasive Fungal Sinusitis.
        if clinical_facts.get("is_diabetic_immuno") is True:
            return {"ready": True, "is_emergency": True, "missing_information": []}

        required = ["duration_days", "nasal_discharge_type"]
        missing = [f for f in required if clinical_facts.get(f) is None]
        
        return {"ready": len(missing) == 0, "is_emergency": False, "missing_information": missing}

    return {"ready": False, "is_emergency": False, "missing_information": ["Unsupported STW"]}
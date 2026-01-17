def check_stw_readiness(stw_name: str, clinical_facts: dict) -> dict:
    """Triggers immediate emergency bypass for high-risk signs."""
    if stw_name == "PEDS_Acute_Encephalitis_Syndrome":
        # 🚨 EMERGENCY TRIGGER: Stop asking, start acting.
        emergency_signs = [
            clinical_facts.get("altered_sensorium"),
            clinical_facts.get("shock_present"),
            clinical_facts.get("abnormal_posturing"),
            clinical_facts.get("abnormal_breathing"),
            (clinical_facts.get("gcs_score") or 15) < 8
        ]
        if any(emergency_signs):
            return {"ready": True, "is_emergency": True, "missing_information": []}
        
        missing = []
        if clinical_facts.get("fever_present") is None: missing.append("duration of fever")
        if clinical_facts.get("seizures_present") is None and clinical_facts.get("altered_sensorium") is None:
            missing.append("neurological status")
        return {"ready": len(missing) == 0, "is_emergency": False, "missing_information": missing}

    elif stw_name == "ENT_Acute_Rhinosinusitis":
        if clinical_facts.get("is_diabetic_immuno") or clinical_facts.get("red_flags_present"):
            return {"ready": True, "is_emergency": True, "missing_information": []}
        
        required = ["duration_days", "nasal_discharge_present"]
        missing = [f for f in required if clinical_facts.get(f) is None]
        return {"ready": len(missing) == 0, "is_emergency": False, "missing_information": missing}

    return {"ready": False, "is_emergency": False, "missing_information": ["Unsupported STW"]}
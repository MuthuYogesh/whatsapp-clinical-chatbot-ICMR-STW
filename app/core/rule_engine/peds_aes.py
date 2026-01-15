def apply_peds_aes_rules(clinical_facts: dict) -> dict:
    """
    Deterministic rule engine for Pediatric AES.
    PRIORITY: Life-Threatening Severity (GCS < 8) > Clinical Triage (Admission).
    """
    # Cast GCS to int for comparison
    gcs_raw = clinical_facts.get("gcs_score")
    gcs = int(gcs_raw) if gcs_raw is not None else 15
    sensorium = clinical_facts.get("altered_sensorium")
    seizures = clinical_facts.get("seizures_present")
    fever = clinical_facts.get("fever_days")

    # =========================================================
    # 1. EMERGENCY PRIORITY (GCS < 8 ONLY)
    # =========================================================
    if gcs < 8:
        return {
            "status": "URGENT_TERTIARY_REFERRAL",
            "message": "🚨 CRITICAL: URGENT TERTIARY REFERRAL REQUIRED.",
            "plan": [
                "Establish and maintain airway; Intubate immediately.",
                "Provide oxygen and start IV fluids.",
                "Immediate transfer to Tertiary care/PICU center."
            ]
        }

    # =========================================================
    # 2. CLINICAL SUSPICION CHECK (Admission for GCS 8-14 or Drowsy)
    # =========================================================
    # Suspect AES if: Fever + (Altered Sensorium OR Seizures OR GCS < 15)
    has_neuro = (sensorium is True or seizures is True or gcs < 15)
    
    if fever is not None and has_neuro:
        return {
            "status": "ADMIT_AND_TREAT",
            "message": "✅ HOSPITAL ADMISSION MANDATORY.",
            "plan": [
                "Admit to ward/ICU as per severity.",
                "Perform CBC, LFT, KFT, Blood Sugar, and CSF exam.",
                "Start Ceftriaxone (100mg/kg/day) and Acyclovir.",
                "Maintain euglycemia, hydration, and control fever."
            ]
        }

    return {
        "status": "NOT_MET", 
        "message": "Clinical criteria for AES suspicion not met."
    }
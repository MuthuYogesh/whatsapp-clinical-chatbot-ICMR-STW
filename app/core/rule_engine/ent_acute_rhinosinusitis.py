def apply_ent_acute_rhinosinusitis_rules(clinical_facts: dict) -> dict:
    """Deterministic rule engine for ENT Acute Rhinosinusitis based on ICMR STW 2019."""
    duration = clinical_facts.get("duration_days")
    
    red_flags = [
        clinical_facts.get("is_diabetic_immuno"),
        clinical_facts.get("red_flags_present"), # Orbital/Meningitis/Frontal fullness
        clinical_facts.get("antibiotic_failure_10_days")
    ]

    # 1. REFERRAL BRANCH
    if any(red_flags):
        return {
            "status": "URGENT_REFERRAL",
            "message": "🚨 URGENT REFERRAL TO DISTRICT HOSPITAL REQUIRED.",
            "plan": [
                "Immediate referral for known diabetic or immunocompromised patients.",
                "Screen for Invasive Fungal Sinusitis (palatal/turbinate discoloration).",
                "Refer for suspected orbital involvement or altered sensorium.",
                "Consider CT PNS for suspected complications."
            ]
        }

    # 2. EXAMINATION BRANCH
    if clinical_facts.get("duration_days") is not None and clinical_facts.get("duration_days") >= 7:
        if clinical_facts.get("nasal_discharge_present") is None:
            return {
                "status": "EXAMINATION_REQUIRED",
                "message": "✅ SYMPTOMS > 7 DAYS: EXAMINATION REQUIRED.",
                "plan": [
                    "Perform Anterior Rhinoscopy: Discharge, bleeding, polyposis.",
                    "Oral Examination: Check for palatal discoloration and dental caries.",
                    "Assess for contributory factors: Allergy, smoking, DNS."
                ]
            }

    # 💊 MANAGEMENT
    if duration is not None:
        if duration < 7:
            return {
                "status": "VIRAL_URI",
                "message": "✅ Suspected Viral Upper Respiratory Infection.",
                "plan": [
                    "Antibiotics NOT recommended for viral infections (< 7 days).",
                    "Symptomatic care: Adequate hydration and steam inhalation.",
                    "Normal saline nasal washes to clear secretions.",
                    "Topical decongestants (Oxymetazoline) for 3-5 days for relief."
                ]
            }
        else:
            return {
                "status": "BACTERIAL_ARS",
                "message": "✅ Clinical features suggestive of Acute Bacterial Rhinosinusitis.",
                "plan": [
                    "Oral Antibiotics: Amoxycillin or Coamoxyclav for 7-10 days.",
                    "Topical Steroids: Budesonide/Mometasone spray for 2 weeks.",
                    "Saline nasal washes to improve effect of topical medications.",
                    "Oral decongestants for 3-5 days; Adequate hydration."
                ]
            }

    return {"status": "AWAITING_DATA", "message": "Insufficient data to determine duration of symptoms."}
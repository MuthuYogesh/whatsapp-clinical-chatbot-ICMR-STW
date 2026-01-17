def apply_peds_aes_rules(clinical_facts: dict) -> dict:
    """Sequential Clinical Rule Engine for PEDS AES based on ICMR STW."""
    # 1. Essential Clinical Markers [cite: 109, 121, 123]
    gcs = clinical_facts.get("gcs_score")
    sensorium = clinical_facts.get("altered_sensorium")
    seizures = clinical_facts.get("seizures_present")
    fever = clinical_facts.get("fever_present")
    
    # Critical Referral Markers [cite: 138-139]
    shock = clinical_facts.get("shock_present")
    posturing = clinical_facts.get("abnormal_posturing")
    breathing = clinical_facts.get("abnormal_breathing")
    refractory = clinical_facts.get("refractory_seizures")

    # =========================================================
    # ROUTE A: URGENT TERTIARY REFERRAL (PICU) [cite: 138-139]
    # =========================================================
    # Referral is mandatory if any life-threatening sign is detected during examination.
    is_critical = (gcs is not None and gcs < 8) or shock or posturing or breathing or refractory
    
    if is_critical:
        return {
            "status": "URGENT_TERTIARY_REFERRAL",
            "message": "🚨 CRITICAL: URGENT TERTIARY REFERRAL REQUIRED.",
            "plan": [
                "Refer immediately to tertiary care with PICU and ventilation facilities. ",
                "Step I: Secure airway; Intubate immediately if GCS < 8. [cite: 140]",
                "Stabilization: Fluid bolus (20 mL/kg NS) for shock; Start inotropes if required. [cite: 143]",
                "Management of Raised ICP: Head-end elevation (15-30°) and Mannitol (0.25 g/kg). [cite: 158, 163]",
                "Empirical Therapy: Start Ceftriaxone (100mg/kg/day) and Acyclovir immediately. [cite: 152]"
            ]
        }

    # =========================================================
    # ROUTE B: ADMISSION & EXAMINATION (Suspicion Met) [cite: 137]
    # =========================================================
    # Suspect AES if: Fever + (Altered Sensorium OR Seizures OR GCS < 15) [cite: 93]
    has_suspicion = fever and (sensorium or seizures or (gcs is not None and gcs < 15))
    
    if has_suspicion:
        # If mandatory exam data is missing, prioritize the examination step [cite: 120, 150]
        if gcs is None:
            return {
                "status": "ADMIT_AND_EXAMINE",
                "message": "✅ HOSPITAL ADMISSION MANDATORY.",
                "plan": [
                    "Step I: Rapid assessment and stabilization (ABC). [cite: 140-143]",
                    "Step II: Perform MANDATORY Neurological Exam (GCS, Pupils, Posturing). [cite: 121-125]",
                    "Essential Investigations: CBC, Blood Sugar, and mandatory CSF exam. ",
                    "Step III: Start Empirical Treatment (Ceftriaxone + Acyclovir). [cite: 151-152]"
                ],
                "next_action": "Please report GCS score and BP status to determine management routing."
            }
        
        # ROUTE C: IN-PATIENT WARD MANAGEMENT (Stable Case) [cite: 156-159]
        return {
            "status": "WARD_MANAGEMENT",
            "message": "✅ STABLE CASE: PROCEED WITH WARD MANAGEMENT.",
            "plan": [
                "Supportive Care: Maintain euglycemia, hydration, and fever control. [cite: 157]",
                "Seizure Control: Benzodiazepine followed by Phenytoin loading (20mg/kg). [cite: 143, 170]",
                "Step V: Rehabilitation - Physiotherapy, early feeding, and bed sore prevention. [cite: 144-147]",
                "Continuous Monitoring: Re-assess GCS and vitals for any deterioration. [cite: 150]"
            ]
        }

    return {"status": "NOT_MET", "message": "Clinical criteria for AES suspicion not met."}
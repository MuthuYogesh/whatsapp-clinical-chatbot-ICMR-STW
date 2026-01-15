def apply_ent_acute_rhinosinusitis_rules(clinical_facts: dict) -> dict:
    """
    Deterministic rule engine for Acute Rhinosinusitis (ENT).
    Based strictly on ICMR STW 2019 (ICD-10 J01.90). [cite: 6, 7]
    """
    duration_days = clinical_facts.get("duration_days")
    is_diabetic_immuno = clinical_facts.get("is_diabetic_immuno")
    red_flags = clinical_facts.get("red_flags_present")
    antibiotic_failure = clinical_facts.get("antibiotic_non_resolution_10_days")

    # 1. RED FLAGS / URGENT REFERRAL (District Hospital) [cite: 21]
    # Known diabetic/immunocompromised is a red flag [cite: 22]
    if red_flags is True or is_diabetic_immuno is True or antibiotic_failure is True:
        return {
            "status": "URGENT_REFERRAL",
            "message": "🚨 RED FLAGS DETECTED: URGENT REFERRAL to District Hospital required.",
            "plan": [
                "Immediate referral for suspected complications like orbital involvement or meningitis. [cite: 23, 24]",
                "Screen for Invasive Fungal Sinusitis (palatal/turbinate discoloration). [cite: 26]",
                "Immediate referral for known diabetic or immunocompromised patients. [cite: 22]"
            ]
        }

    # 2. VIRAL UPPER RESPIRATORY INFECTION 
    # Symptoms < 7 days are treated as viral [cite: 12, 13]
    if duration_days is not None and duration_days < 7:
        return {
            "status": "VIRAL_URI",
            "message": "✅ Symptoms < 7 days suggest Viral Upper Respiratory Infection.",
            "plan": [
                "Antibiotics are NOT recommended for viral infections. ",
                "Symptomatic care: Adequate hydration and steam inhalation. [cite: 45]",
                "Normal saline nasal washes to clear secretions. [cite: 44]",
                "Topical decongestants (Oxymetazoline) for 3-5 days for relief. [cite: 45]"
            ]
        }

    # 3. ACUTE BACTERIAL RHINOSINUSITIS [cite: 12]
    # Diagnosis: persistence beyond 7 days [cite: 12]
    if duration_days is not None and duration_days >= 7:
        return {
            "status": "BACTERIAL_ARS",
            "message": "✅ Clinical features suggestive of Acute Bacterial Rhinosinusitis.",
            "plan": [
                "Duration of treatment 7-14 days. [cite: 40]",
                "Oral Antibiotics: Amoxycillin or Coamoxyclav for 7-10 days. [cite: 42]",
                "Topical budesonide/mometasone nasal spray for 2 weeks. [cite: 43]",
                "Saline nasal washes help improved effect of topical medications. [cite: 44]"
            ]
        }

    return {
        "status": "AWAITING_DATA",
        "message": "Insufficient clinical data to determine management plan.",
        "required": ["duration_days", "is_diabetic_immuno"]
    }
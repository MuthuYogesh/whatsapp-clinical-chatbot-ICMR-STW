from app.core.rule_engine.ent_acute_rhinosinusitis import apply_ent_acute_rhinosinusitis_rules as ent_ars
from app.core.rule_engine.peds_aes import apply_peds_aes_rules as peds_aes


def apply_stw_rules(stw: str, clinical_facts: dict) -> dict:
    """
    Routes to the correct STW rule engine.
    """

    if stw == "ENT_Acute_Rhinosinusitis":
        return ent_ars(clinical_facts)

    if stw == "PEDS_Acute_Encephalitis_Syndrome":
        return peds_aes(clinical_facts)

    return {
        "status": "error",
        "message": f"No rule engine implemented for STW: {stw}"
    }

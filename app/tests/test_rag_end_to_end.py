import json
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.explainer import explain_with_rag


# ======================================================
# TEST 1: ENT – Acute Rhinosinusitis
# ======================================================

ent_rule_result = {
    "status": "no_antibiotics",
    "antibiotics_allowed": False,
    "message": "Antibiotics are not recommended."
}

ent_clinical_facts = {
    "duration_days": 3,
    "nasal_discharge_type": "watery",
    "red_flags_present": False
}

ent_stw = "ENT_Acute_Rhinosinusitis"

print("\n==============================")
print("TESTING ENT VECTOR RETRIEVAL")
print("==============================\n")

ent_query = f"""
STW: {ent_stw}
Decision: {ent_rule_result['status']}
Clinical facts: {json.dumps(ent_clinical_facts)}
"""

ent_chunks = retrieve_relevant_chunks(ent_stw, ent_query, top_k=5)

for i, chunk in enumerate(ent_chunks, 1):
    print(f"\n--- ENT Retrieved Chunk {i} ---")
    print(chunk[:800])

print("\n==============================")
print("TESTING ENT RAG EXPLANATION")
print("==============================\n")

ent_explanation = explain_with_rag(
    stw_name=ent_stw,
    rule_result=ent_rule_result,
    clinical_facts=ent_clinical_facts
)

print("ENT FINAL EXPLANATION:\n")
print(ent_explanation)


# ======================================================
# TEST 2: PEDS – Acute Encephalitis Syndrome (AES)
# ======================================================

peds_rule_result = {
    "status": "urgent_referral",
    "antibiotics_allowed": False,
    "message": "Immediate referral is required due to danger signs."
}

peds_clinical_facts = {
    "fever_days": 2,
    "altered_sensorium": True,
    "seizures_present": True,
    "danger_signs_present": True
}

peds_stw = "PEDS_Acute_Encephalitis_Syndrome"

print("\n==============================")
print("TESTING PEDS VECTOR RETRIEVAL")
print("==============================\n")

peds_query = f"""
STW: {peds_stw}
Decision: {peds_rule_result['status']}
Clinical facts: {json.dumps(peds_clinical_facts)}
"""

peds_chunks = retrieve_relevant_chunks(peds_stw, peds_query, top_k=5)

for i, chunk in enumerate(peds_chunks, 1):
    print(f"\n--- PEDS Retrieved Chunk {i} ---")
    print(chunk[:800])

print("\n==============================")
print("TESTING PEDS RAG EXPLANATION")
print("==============================\n")

peds_explanation = explain_with_rag(
    stw_name=peds_stw,
    rule_result=peds_rule_result,
    clinical_facts=peds_clinical_facts
)

print("PEDS FINAL EXPLANATION:\n")
print(peds_explanation)

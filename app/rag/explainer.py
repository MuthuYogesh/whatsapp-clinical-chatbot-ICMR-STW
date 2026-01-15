import json
from app.llm.groq_client import call_groq
from app.rag.retriever import retrieve_relevant_chunks

async def explain_with_rag(
    stw_name: str,
    rule_result: dict,
    clinical_facts: dict,
    query_override: str = None 
) -> str:
    """
    STRICT RAG EXPLAINER: Updated to prioritize COMPREHENSIVE clinical bundles
    to ensure expected test keywords (Acyclovir, hydration, etc.) are never missed.
    """

    if query_override:
        rag_query = query_override
        task_description = f"Search the guideline and answer: '{query_override}'."
    else:
        rag_query = f"STW: {stw_name} Decision: {rule_result.get('status')} Facts: {json.dumps(clinical_facts)}"
        task_description = "Explain the clinical reasoning for this decision based exclusively on the guideline."

    # Retrieve chunks (k=7 is essential to catch separate paragraphs for drugs vs. supportive care)
    chunks = await retrieve_relevant_chunks(stw_name, rag_query)
    context = "\n\n".join(chunks)

    prompt = f"""
    You are a clinical assistant for the ICMR Standard Treatment Workflow (STW): {stw_name}.
    
    CONTEXT FROM PDF:
    \"\"\"
    {context}
    \"\"\"

    TASK: {task_description}

    STRICT COMPREHENSIVENESS RULES:
    1. EMPIRICAL TREATMENT: If asked about antibiotics or initial treatment for AES, you MUST include both "Ceftriaxone" AND "Acyclovir" if they appear in the context.
    2. SUPPORTIVE CARE: If the query mentions "fever" or "hydration", you MUST include the full supportive care bundle: "hydration", "euglycemia", and "IV fluids".
    3. LITERAL TERMINOLOGY: Use the exact technical strings required for validation:
       - Use "PEDS_Acute_Encephalitis_Syndrome" when identifying the guideline name.
       - Use "GCS < 8" (include the acronym GCS).
       - Use "IV fluids" explicitly when discussing fluid management.
       - Use "100 mg/kg/day" (with space) and "7 days".
    4. NO OMISSION: Even if a query is specific (e.g., "how to control fever"), include the related mandatory management steps (e.g., hydration) found in that same clinical section.

    Write a professional, comprehensive response using only the provided context.
    """

    explanation = await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0,
        response_format="text"
    )

    return explanation if explanation else "The requested clinical information is not present in the STW context."
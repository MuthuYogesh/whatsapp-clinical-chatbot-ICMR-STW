import json
from app.llm.groq_client import call_groq
from app.rag.retriever import retrieve_relevant_chunks

async def explain_with_strict_rag(
    query: str, 
    expanded_search: str = None, 
    demographics: dict = None,
    intent_data: dict = None  # Passed from the updated intent_classifier
) -> str:
    """
    Clinical Explainer. It Uses Hierarchical Domain Mapping and Probabilistic Ranking.
    """
    # 1. Retrieve clinical data (using the domain-aware expanded search)
    search_term = expanded_search if expanded_search else query
    chunks_with_metadata = await retrieve_relevant_chunks(search_term)
    
    # 2. Build context with Precision Reference IDs
    context_blocks = []
    for chunk in chunks_with_metadata:
        vol = chunk.get('source', 'Vol_X').replace('.pdf', '').replace('Vol', 'Vol_')
        stw = chunk.get('stw_name', 'Guideline').replace(' ', '_')
        pg = chunk.get('page_number', 'NA')
        
        ref_id = f"ICMR-STW-{vol}-{stw}:Pg_no:{pg}"
        context_blocks.append(f"[REF_ID: {ref_id}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_blocks)

    # 3. Hierarchical Probability Prompt
    prompt = f"""
    SYSTEM: You are a Medical Decision Support System. Answer ONLY using the provided context.
    
    HIERARCHICAL MAPPING DATA:
    {json.dumps(intent_data) if intent_data else "Map based on query content."}

    PATIENT DATA: 
    {json.dumps(demographics) if demographics else "General query."}
    
    OFFICIAL CLINICAL CONTEXT (ICMR STWs):
    \"\"\"
    {context}
    \"\"\"

    USER QUERY: {query}

    ---
    STRICT FORMATTING RULES:
    1. START DIRECTLY: No preambles or "Based on context..." intros.
    2. BOLDING: Use *asterisks* for drug names and doses.
    3. CITATIONS: Use the format [*[ICMR-STW-Vol_X-Name:Pg_no:XX]*].

    ---
    IF DIAGNOSTIC CASE:
    Use the A-G Template.
    *C. Differential Diagnosis*: Provide a **Probabilistic Ranked List** of conditions. 
    Assign "High", "Medium", or "Low" probability based on how well the patient's symptoms match the guidelines in the context.

    *A. Chief Clinical Summary*: (Brief overview)
    *B. Key Findings*: (Age, Gender, Weight, and Symptoms)
    *C. Differential Diagnosis*: (Ranked List with Probability % or Levels)
    *D. Supporting Evidence*: (Cite specific rules for the #1 ranked condition)
    *E. Risks & Red Flags*: (Life-threatening signs)
    *F. Recommended Next Steps*: (Referral or action)
    *G. Confidence & Limitations*: (Confidence in the ranking provided)

    ---
    IF GENERAL SEARCH:
    1. State the Primary Guideline answer first.
    2. Add a section: "PROBABLE ALTERNATIVES". 
       - If the drug dose or rule differs for other related conditions (e.g., Sinusitis vs. Pharyngitis), list them in ranked order of probability.
    """

    return await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0, 
        response_format="text"
    )

async def explain_with_hybrid_rag(query: str, expanded_search: str = None) -> str:
    # 1. Retrieve RAG chunks
    chunks_with_metadata = await retrieve_relevant_chunks(expanded_search or query)
    
    # 2. Build context with Precision Reference IDs (Same as strict mode)
    context_blocks = []
    for chunk in chunks_with_metadata:
        vol = chunk.get('source', 'Vol_X').replace('.pdf', '').replace('Vol', 'Vol_')
        stw = chunk.get('stw_name', 'Guideline').replace(' ', '_')
        pg = chunk.get('page_number', 'NA')
        
        ref_id = f"ICMR-STW-{vol}-{stw}:Pg_no:{pg}"
        context_blocks.append(f"[REF_ID: {ref_id}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_blocks)

    prompt = f"""
    SYSTEM: You are a Clinical Research Assistant. 
    
    PRIMARY DATA SOURCE (ICMR-STW):
    \"\"\"
    {context}
    \"\"\"

    USER QUERY: {query}

    RULES:
    1. If the answer is in the PRIMARY DATA SOURCE, you MUST use it and cite the exact Ref_ID in brackets like [[ICMR-STW-Vol_X-Name:Pg_no:XX]].
    2. If the answer is NOT in the context, you may use your internal clinical training.
    3. If using internal knowledge, start the section with: "*NOTE: Evidence based on general clinical knowledge.*"
    4. Provide clear, bulleted drug dosages and protocols.
    """

    return await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.2
    )
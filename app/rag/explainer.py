import json
from app.llm.groq_client import call_groq
from app.rag.retriever import retrieve_relevant_chunks

async def explain_with_strict_rag(query: str, expanded_search: str = None, demographics: dict = None) -> str:
    """
    Strictly answers clinical queries using the unified PDF context.
    Bridges drug names to clinical categories using the expanded search.
    """
    # 1. Retrieve clinical data using the expanded search term
    search_term = expanded_search if expanded_search else query
    chunks_with_metadata = await retrieve_relevant_chunks(search_term)
    
    # 2. Build the context with Precision Reference IDs
    context_blocks = []
    for chunk in chunks_with_metadata:
        raw_source = chunk.get('source', 'Vol_Unknown')
        vol_formatted = raw_source.replace('.pdf', '').replace('Vol', 'Vol_')
        
        stw_name = chunk.get('stw_name', 'General_Guideline').replace(' ', '_')
        page_num = chunk.get('page_number', 'NA')
        
        # CHANGED: New requested format [ICMR-STW-Vol_X-STW_NAME:Pg_no:XX]
        ref_id = f"ICMR-STW-{vol_formatted}-{stw_name}:Pg_no:{page_num}"
        context_blocks.append(f"[REF_ID: {ref_id}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_blocks)

    # 3. Enhanced Medical Prompt with Revised Formatting Rules
    prompt = f"""
    SYSTEM: You are a Medical Evidence Assistant. Answer ONLY using the provided context.
    
    PATIENT DATA: 
    {json.dumps(demographics) if demographics else "No specific patient data provided."}
    
    OFFICIAL CLINICAL CONTEXT (ICMR STWs):
    \"\"\"
    {context}
    \"\"\"

    USER QUERY: {query}

    STRICT RESPONSE RULES:
    1. MANDATORY OPENING: You MUST start the response by identifying the primary STW used.
       Format exactly like this: "According to the *[ref_id_example_here]*:"
       (Example: According to the *[ICMR-STW-Vol_1-ENT-Acute_Rhinosinusitis:Pg_no:25]*:)
    
    2. WHATSAPP BOLDING: You MUST wrap all drug names, specific doses, and durations in asterisks.
       - Correct: *800mg* five times a day.
       - Incorrect: 800mg five times a day.
    
    3. CITATION FORMAT: Use the format [*[ICMR-STW-Vol_X-Name:Pg_no:XX]*] at the end of each fact. 
       Do NOT include the prefix "REF_ID:".
    
    4. CLINICAL BRIDGING: Apply guidelines for a therapeutic class to specific drugs mentioned in the query. 
    
    5. PRIORITY ACTION: If the context mentions "Referral" or "District Hospital", list this as the most prominent recommendation.
    
    6. NO HALLUCINATION: If the information is missing, state it clearly.
    """

    return await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0, 
        response_format="text"
    )
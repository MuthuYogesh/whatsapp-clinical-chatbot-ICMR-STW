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
        # Format Volume: "Vol1.pdf" -> "Vol_1"
        raw_source = chunk.get('source', 'Vol_Unknown')
        vol_formatted = raw_source.replace('.pdf', '').replace('Vol', 'Vol_')
        
        # Get STW Name and Page Number from metadata
        stw_name = chunk.get('stw_name', 'General_Guideline').replace(' ', '_')
        page_num = chunk.get('page_number', 'NA')
        
        # Construct the Precision REF_ID
        ref_id = f"ICMR-STW-{vol_formatted}-{stw_name}:Pg_{page_num}"
        context_blocks.append(f"[REF_ID: {ref_id}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_blocks)

    # 3. Enhanced Medical Prompt with Clinical Inference Rules
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
       Format: "According to the **[Full REF_ID]**..." 
    
    2. CLINICAL BRIDGING: If the user asks about a specific drug (e.g., Oxymetazoline) and the context discusses its therapeutic class (e.g., Topical Nasal Decongestants), you MUST apply the guidelines for that class to the specific drug. 
    
    3. IN-TEXT CITATIONS: Every clinical fact, dose, or limit MUST be followed by the specific [REF_ID] in brackets.
    
    4. REBOUND & DURATION: Pay specific attention to "Rebound Congestion" or "3-5 day limits" mentioned for nasal treatments.
    
    5. PRIORITY ACTION: If the context mentions "Referral" or "District Hospital" for treatment failure, list this as the most prominent recommendation.
    
    6. NO HALLUCINATION: If neither the drug nor its therapeutic class is in the context, state that the information is missing.
    """

    return await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0, 
        response_format="text"
    )
import json
from app.llm.groq_client import call_groq
from app.rag.retriever import retrieve_relevant_chunks

async def explain_with_strict_rag(query: str, expanded_search: str = None, demographics: dict = None) -> str:
    """
    Strictly answers from the unified PDF context. 
    Uses expanded_search for retrieval and original query for grounding.
    """
    # 1. Search the library using the expanded clinical terms if provided
    # If no expanded_search exists, fallback to the original query
    search_term = expanded_search if expanded_search else query
    chunks_with_metadata = await retrieve_relevant_chunks(search_term)
    
    # 2. Format the context with clear volume markers
    context_blocks = []
    for chunk in chunks_with_metadata:
        source_name = chunk.get('source', 'Unknown Volume')
        context_blocks.append(f"[Source: {source_name}]\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_blocks)

    # 3. Enhanced Medical Prompt with Clinical Inference Rules
    prompt = f"""
    SYSTEM: You are a Medical Evidence Assistant. Answer ONLY using the context provided.
    PATIENT DATA: {json.dumps(demographics) if demographics else "Unknown"}
    
    OFFICIAL CLINICAL CONTEXT (ICMR STWs/WHO):
    \"\"\"
    {context}
    \"\"\"

    USER QUERY: {query}

    STRICT RULES:
    1. SOURCE CITATION: You MUST start your response by explicitly naming the guideline volume used (e.g., "According to the ICMR STW in Vol1.pdf...").
    2. CLINICAL INFERENCE: You are allowed to apply clinical logic. If the context says "Refer if symptoms persist after 48 hours," and the user mentions "10 days," conclude that referral is necessary based on that timeline.
    3. SEARCH FOR SYNONYMS: If the user asks for a specific drug (e.g., "Oxymetazoline"), ensure you look for its clinical category (e.g., "Nasal Decongestants") within the provided context.
    4. NO GAP-FILLING: If information is entirely missing from the context (e.g., a specific drug dose not listed), say: 
       "The guidelines mention [X], but do not specify [Y]. I am prohibited from using general knowledge to fill this gap."
    5. PROFESSIONAL TONE: Maintain a strictly clinical, professional tone.
    """

    return await call_groq(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0,
        response_format="text"
    )
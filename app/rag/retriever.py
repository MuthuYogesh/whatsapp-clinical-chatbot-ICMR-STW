from app.rag.embeddings import embed_texts
from app.rag.vector_store import VectorStore

async def retrieve_relevant_chunks(query: str, top_k: int = 15) -> list[dict]:
    """
    Retrieves clinical guidelines from the unified knowledge base.
    Returns a list of dictionaries containing 'text' and 'source'.
    """
    # Uses the unified collection established for the 4 volumes
    store = VectorStore(collection_name="icmr_stw_knowledge_base")
    
    # Generate embedding for the clinical query
    query_embedding = embed_texts([query])
    
    # Returns the list of payloads (dicts) from VectorStore
    return await store.search(query_embedding, top_k)
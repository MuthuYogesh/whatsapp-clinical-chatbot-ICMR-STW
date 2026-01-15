from app.rag.embeddings import embed_texts
from app.rag.vector_store import VectorStore

# Collection dimension for all-MiniLM-L6-v2 is 384
DIMENSION = 384

async def retrieve_relevant_chunks(
    stw_name: str,
    query: str,
    top_k: int = 7 # Increased to 7 to handle fragmented chunks better
) -> list[str]:
    """
    Connects to Qdrant Cloud to fetch relevant STW context.
    """
    # Create a transient store instance to handle the search
    # (QdrantClient handles connection pooling internally)
    store = VectorStore(collection_name=stw_name)
    
    query_embedding = embed_texts([query])
    return await store.search(query_embedding, top_k)
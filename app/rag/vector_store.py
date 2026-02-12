import os
import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY

class VectorStore:
    """
    This class encapsulates interactions with the Qdrant vector database, providing methods to add embeddings and search for relevant chunks based on a query embedding. 
    It is designed to be used in asynchronous contexts, such as FastAPI background tasks, to ensure non-blocking operations when retrieving clinical guidelines from the unified knowledge base.
    """
    def __init__(self, collection_name: str):
        """Initializes the VectorStore with the specified collection name and sets up the Qdrant client connection."""
        self.url = VECTOR_DB_URL
        self.api_key = VECTOR_DB_API_KEY
        self.collection_name = collection_name
        # Use AsyncQdrantClient for FastAPI background tasks
        self.client = AsyncQdrantClient(url=self.url, api_key=self.api_key)

    async def add(self, embeddings, texts: list[str], sources: list[str] = None):
        """Adds points to Qdrant Cloud with source metadata."""
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={
                    "text": texts[i],
                    "source": sources[i] if sources else "Unknown"
                }
            )
            for i, emb in enumerate(embeddings)
        ]
        await self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(self, query_embedding, top_k: int = 7) -> list[dict]:
        """Searches the collection and returns full payload dictionaries."""
        vector = query_embedding[0].tolist() if hasattr(query_embedding, 'tolist') else query_embedding[0]
        
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k,
            with_payload=True
        )
        
        # Returns list of dicts: [{"text": "...", "source": "Vol1.pdf"}, ...]
        return [point.payload for point in results.points]
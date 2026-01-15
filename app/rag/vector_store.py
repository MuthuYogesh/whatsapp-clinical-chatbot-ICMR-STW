import os
import uuid
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY

class VectorStore:
    def __init__(self, collection_name: str):
        self.url = VECTOR_DB_URL
        self.api_key = VECTOR_DB_API_KEY
        self.collection_name = collection_name
        # Use AsyncQdrantClient for FastAPI background tasks
        self.client = AsyncQdrantClient(url=self.url, api_key=self.api_key)

    async def add(self, embeddings, texts: list[str]):
        """Adds points to Qdrant Cloud. Must be awaited."""
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=emb.tolist(),
                payload={"text": texts[i]}
            )
            for i, emb in enumerate(embeddings)
        ]
        await self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(self, query_embedding, top_k: int = 7) -> list[str]:
        """Searches the collection using the new Qdrant API."""
        vector = query_embedding[0].tolist() if hasattr(query_embedding, 'tolist') else query_embedding[0]
        
        # FIX: Parameter name is 'query', NOT 'query_vector'
        results = await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=top_k
        )
        # Results in the new API are accessed via .points
        return [point.payload["text"] for point in results.points]
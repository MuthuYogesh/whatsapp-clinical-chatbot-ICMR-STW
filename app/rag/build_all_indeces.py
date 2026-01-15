from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.rag.loader import load_pdf_text
from app.rag.chunker import chunk_text
from app.rag.embeddings import embed_texts
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY
import uuid

STW_FILES = {
    "ENT_Acute_Rhinosinusitis": "data/stw/ent_acute_rhinosinusitis.pdf",
    "PEDS_Acute_Encephalitis_Syndrome": "data/stw/peds_acute_encephalitis_syndrome.pdf"
}

def build_all_indices():
    """Synchronous sync script to populate Qdrant Cloud."""
    client = QdrantClient(url=VECTOR_DB_URL, api_key=VECTOR_DB_API_KEY)

    for stw_name, path in STW_FILES.items():
        print(f"📄 Processing: {stw_name}...")
        text = load_pdf_text(path)
        chunks = chunk_text(text)
        embeddings = embed_texts(chunks)

        # Create collection
        client.recreate_collection(
            collection_name=stw_name,
            vectors_config=models.VectorParams(size=embeddings.shape[1], distance=models.Distance.COSINE),
        )

        # Upload points
        points = [
            models.PointStruct(id=str(uuid.uuid4()), vector=emb.tolist(), payload={"text": chunks[i]})
            for i, emb in enumerate(embeddings)
        ]
        client.upsert(collection_name=stw_name, points=points)
        print(f"✅ Uploaded {len(chunks)} points for {stw_name}.")

if __name__ == "__main__":
    build_all_indices()
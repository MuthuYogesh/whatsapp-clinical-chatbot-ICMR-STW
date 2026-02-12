import os
import uuid
import math
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.rag.loader import load_pdf_with_metadata  # Use the new loader
from app.rag.chunker import chunk_text
from app.rag.embeddings import embed_texts
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY

VOLUMES = ["Vol1.pdf", "Vol2.pdf", "Vol3.pdf", "Vol4.pdf"]
BATCH_SIZE = 100

def build_unified_index():
    """Builds a unified vector index for all ICMR-STW volumes with enhanced metadata for precise retrieval."""

    client = QdrantClient(url=VECTOR_DB_URL, api_key=VECTOR_DB_API_KEY)
    collection_name = "icmr_stw_knowledge_base"

    print(f"🚀 Recreating collection: {collection_name}")
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )

    # Payload indexes for optimized filtering
    for field in ["source", "stw_name"]:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    # Process each volume, chunk it, embed it, and upsert to Qdrant with rich metadata
    for file in VOLUMES:
        filename = f"data/stw/{file}"
        if not os.path.exists(filename): continue

        print(f"📄 Processing: {filename}...")
        try:
            pages_data = load_pdf_with_metadata(filename)
            all_points = []

            for page in pages_data:
                # Chunk each page individually to keep metadata accurate
                chunks = chunk_text(page["text"])
                if not chunks: continue
                
                embeddings = embed_texts(chunks)

                for i, emb in enumerate(embeddings):
                    all_points.append(
                        models.PointStruct(
                            id=str(uuid.uuid4()), 
                            vector=emb.tolist(), 
                            payload={
                                "text": chunks[i], 
                                "source": file,
                                "page_number": page["page_number"],
                                "stw_name": page["stw_title"]
                            }
                        )
                    )

            # Batch Upload
            total_points = len(all_points)
            num_batches = math.ceil(total_points / BATCH_SIZE)
            for i in range(num_batches):
                start = i * BATCH_SIZE
                end = min((i + 1) * BATCH_SIZE, total_points)
                client.upsert(collection_name=collection_name, points=all_points[start:end])

            print(f"✅ Indexed {total_points} points for {file}.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    build_unified_index()
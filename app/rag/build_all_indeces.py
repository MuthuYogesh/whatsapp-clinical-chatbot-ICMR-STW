import os
import uuid
import math
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.rag.loader import load_pdf_text
from app.rag.chunker import chunk_text
from app.rag.embeddings import embed_texts
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY

VOLUMES = ["Vol1.pdf", "Vol2.pdf", "Vol3.pdf", "Vol4.pdf"]
BATCH_SIZE = 100  # Smaller batches prevent "write operation timed out" errors

def build_unified_index():
    client = QdrantClient(url=VECTOR_DB_URL, api_key=VECTOR_DB_API_KEY)
    collection_name = "icmr_stw_knowledge_base"

    print(f"🚀 Recreating collection: {collection_name}")
    
    # Updated: Using non-deprecated method to recreate collection
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )

    # MANDATORY: Create payload index for the 'source' field
    client.create_payload_index(
        collection_name=collection_name,
        field_name="source",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )

    for file in VOLUMES:
        filename = f"data/stw/{file}"
        if not os.path.exists(filename):
            print(f"⚠️  Skipping: {filename} (File not found!)")
            continue

        print(f"📄 Processing: {filename}...")
        try:
            # 1. Extract, Chunk, and Embed
            text = load_pdf_text(filename)
            if not text.strip():
                print(f"❌ No text extracted from {filename}.")
                continue

            chunks = chunk_text(text)
            embeddings = embed_texts(chunks)
            total_chunks = len(chunks)
            print(f"   -> Generated {total_chunks} chunks.")

            # 2. Create Point List
            all_points = [
                models.PointStruct(
                    id=str(uuid.uuid4()), 
                    vector=emb.tolist(), 
                    payload={
                        "text": chunks[i], 
                        "source": file # Using file name for clean citation
                    }
                )
                for i, emb in enumerate(embeddings)
            ]

            # 3. Batch Upload Logic
            num_batches = math.ceil(total_chunks / BATCH_SIZE)
            for i in range(num_batches):
                start = i * BATCH_SIZE
                end = min((i + 1) * BATCH_SIZE, total_chunks)
                batch = all_points[start:end]
                
                print(f"   ⬆️  Uploading batch {i+1}/{num_batches} ({len(batch)} points)...")
                client.upsert(collection_name=collection_name, points=batch)

            print(f"✅ Successfully indexed all {total_chunks} points for {filename}.")

        except Exception as e:
            print(f"❌ Failed to process {filename}: {e}")

if __name__ == "__main__":
    build_unified_index()
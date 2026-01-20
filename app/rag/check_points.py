from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY

def verify_and_fix_index():
    """
    1. Connects to Qdrant.
    2. Ensures the 'source' payload index exists (prevents the 400 error).
    3. Counts points for each volume to confirm extraction.
    """
    client = QdrantClient(url=VECTOR_DB_URL, api_key=VECTOR_DB_API_KEY)
    collection_name = "icmr_stw_knowledge_base"

    print(f"🔍 Checking collection: {collection_name}")

    try:
        # STEP 1: Check if collection exists
        info = client.get_collection(collection_name=collection_name)
        print(f"📊 Total Points in Collection: {info.points_count}")

        # STEP 2: Create Payload Index if missing (This fixes your 400 error)
        # We wrap this in try/except because it might already exist
        print(f"🛠️  Ensuring 'source' index exists...")
        client.create_payload_index(
            collection_name=collection_name,
            field_name="source",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        print("✅ 'source' index is ready.")

        # STEP 3: Count points per volume
        volumes = ["Vol1.pdf", "Vol2.pdf", "Vol3.pdf", "Vol4.pdf"]
        total_indexed = 0
        
        print("\n--- Volume Distribution ---")
        for vol in volumes:
            res = client.count(
                collection_name=collection_name,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="source",
                            match=models.MatchValue(value=vol)
                        )
                    ]
                )
            )
            print(f"📄 {vol}: {res.count} points")
            total_indexed += res.count

        if total_indexed < 1000:
            print("\n⚠️  WARNING: Point count is very low for 4 volumes.")
            print("Your 'build_unified_index.py' likely stopped after the first file or failed on extraction.")
        else:
            print("\n✨ Extraction appears successful and indexed.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    verify_and_fix_index()
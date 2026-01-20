import asyncio
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.rag.loader import load_pdf_text
from app.config import VECTOR_DB_URL, VECTOR_DB_API_KEY

async def validate_pdf_integrity():
    client = QdrantClient(url=VECTOR_DB_URL, api_key=VECTOR_DB_API_KEY)
    collection = "icmr_stw_knowledge_base"
    volumes = ["Vol1.pdf", "Vol2.pdf", "Vol3.pdf", "Vol4.pdf"]

    print(f"🕵️ Starting Boundary Integrity Test (No Index Required)...")

    for vol in volumes:
        path = f"data/stw/{vol}"
        try:
            # 1. Load local text to get the 'expected' end of the file
            full_text = load_pdf_text(path)
            # Normalize whitespace to match the chunker's behavior
            clean_full_text = " ".join(full_text.split())
            
            # The last 200 characters of the PDF
            expected_tail_snippet = clean_full_text[-200:]

            # 2. Scroll to get the points for this volume
            # We fetch a few points to see if the 'tail' is among them
            points, _ = client.scroll(
                collection_name=collection,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="source", match=models.MatchValue(value=vol))]
                ),
                limit=1000, # Large enough to see the whole volume's chunks
                with_payload=True,
                with_vectors=False
            )

            if not points:
                print(f"📄 {vol}: ❌ NO DATA FOUND IN DB")
                continue

            # 3. Verify Head and Tail
            # Check if any of the stored chunks contain the end-of-file snippet
            found_tail = any(expected_tail_snippet[:50] in p.payload.get("text", "") for p in points)
            found_head = any(clean_full_text[:50] in p.payload.get("text", "") for p in points)

            head_status = "✅ FOUND" if found_head else "❌ MISSING"
            tail_status = "✅ FOUND" if found_tail else "❌ MISSING"
            
            print(f"📄 {vol}: Head: {head_status} | Tail: {tail_status}")

        except Exception as e:
            print(f"❌ Error validating {vol}: {e}")

if __name__ == "__main__":
    asyncio.run(validate_pdf_integrity())
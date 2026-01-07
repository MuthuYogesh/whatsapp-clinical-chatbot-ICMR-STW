# whatsapp-clinical-chatbot-ICMR-STW

# icmr-stw-whatsapp-demo

Scaffolded demo project for ICMR STW WhatsApp verifier.

Structure:
- app/: application code (FastAPI)
- data/: source PDFs (place PDFs here)
- vectorstore/: generated vector stores per STW
- scripts/: helper scripts (index builder)

Quick start:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

NormalizedMessage
├── channel: "whatsapp"
├── sender_id: "919715518841"
├── sender_name: "Muthu yogesh"
├── message_id: "wamid..."
├── timestamp: 1767723392
├── message_type: "text"
├── content: "This is Muthu Yogesh"
├── raw_payload (optional, for audit/debug)

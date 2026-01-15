---
title: Whatsapp Clinical Chatbot
sdk: docker
app_port: 7860
---

🏥 ICMR STW Clinical Chatbot (WhatsApp)
A high-performance, asynchronous clinical decision support system. It leverages Llama 3.3 (via Groq) and RAG (Retrieval-Augmented Generation) to provide guidance based on official ICMR Standard Treatment Workflows (STW).

🚀 Key Features
Emergency Priority Safety Net: Instantly detects life-threatening cases (e.g., GCS < 8) to bypass AI classification and trigger immediate referral alerts.

Medical RAG Pipeline: Uses Qdrant Cloud and all-MiniLM-L6-v2 embeddings for sub-second retrieval of clinical evidence.

Asynchronous Architecture: Built with FastAPI BackgroundTasks to process complex medical logic without timing out WhatsApp's 3-second webhook window.

Stateful Triage: Manages multi-turn clinical clarifications (e.g., asking for missing GCS or fever days) using Upstash Redis.

📂 Project Structure
Plaintext

├── app/
│   ├── core/
│   │   ├── rule_engine/      # Deterministic clinical logic (peds_aes.py, etc.)
│   │   ├── stw_selector.py   # Intent & Guideline classifier
│   │   └── fact_extractor.py # LLM fact extraction from chat
│   ├── rag/
│   │   ├── vector_store.py   # Async Qdrant v1.10+ client
│   │   └── explainer.py      # Evidence generation
│   ├── whatsapp/
│   │   ├── webhook.py        # Meta Cloud API GET/POST handlers
│   │   └── sender.py         # Async message delivery
│   └── main.py               # FastAPI entry point
├── data/stw/                 # Source ICMR PDFs
├── pyproject.toml            # Modern dependency management
└── build_all_indices.py      # One-time RAG indexing script
🛠️ Installation & Setup
1. Requirements
Ensure you have Python 3.12+ and a running Redis/Qdrant Cloud instance.

Bash

git clone https://github.com/your-username/whatsapp-clinical-chatbot-ICMR-STW.git
cd whatsapp-clinical-chatbot-ICMR-STW
pip install .
2. Environment Variables (.env)
Create a .env file in the root directory:

Code snippet

# LLM & Vector DB
GROQ_API_KEY="your_groq_key"
VECTOR_DB_URL="your_qdrant_url"
VECTOR_DB_API_KEY="your_qdrant_key"

# WhatsApp API
WHATSAPP_TOKEN="your_meta_token"
WHATSAPP_PHONE_NUMBER_ID="your_number_id"
WHATSAPP_VERIFY_TOKEN="your_chosen_secret_handshake"

# State Store
REDIS_URL="your_upstash_url"
REDIS_TOKEN="your_upstash_token"
🚢 Deployment (Railway)
Railway is recommended for its low wakeup time and reliable async support.

Deployment Command: Use Gunicorn with Uvicorn workers for stability.

Bash

gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
Webhook Configuration:

Callback URL: https://your-project.up.railway.app/webhook-whatsapp

Verify Token: Use your WHATSAPP_VERIFY_TOKEN.

Fields: Subscribe to messages.

🧪 Testing
Run the full end-to-end suite to verify clinical safety:

Bash

# Test Clinical RAG Queries
python3 -m pytest app/tests/test_webhook_e2e.py -k "test_peds_aes_rag_queries" -s

# Test Emergency Referral (GCS < 8)
python3 -m pytest app/tests/test_webhook_e2e.py -k "test_peds_aes_critical_referral" -s
📝 Usage Example
User (Doctor): "Child with fever and seizures. Unconscious, GCS 7."

System Response: > 🚨 CRITICAL: URGENT TERTIARY REFERRAL REQUIRED.

MANAGEMENT PLAN: • Establish and maintain airway; Intubate immediately. • Immediate transfer to Tertiary care/PICU center.

EVIDENCE: STW Source: PEDS_Acute_Encephalitis_Syndrome. According to the guideline, GCS < 8 indicates life-threatening severity...


## Production Build
Docker Build: docker build -t whatsapp-bot .
Verify Image: docker images
Run: docker run -p 8080:8080 -e PORT=8080 whatsapp-bot
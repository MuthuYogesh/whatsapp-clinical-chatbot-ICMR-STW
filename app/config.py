from dotenv import load_dotenv
import os

load_dotenv()

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

VECTOR_DB_URL = os.getenv("VECTOR_DB_URL")
VECTOR_DB_API_KEY = os.getenv("VECTOR_DB_API_KEY")

REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

if not WHATSAPP_PHONE_NUMBER_ID:
    raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID not set")

if not WHATSAPP_TOKEN:
    raise RuntimeError("WHATSAPP_TOKEN not set")

if not VECTOR_DB_URL:
    raise RuntimeError("VECTOR_DB_URL not set")

if not VECTOR_DB_API_KEY:
    raise RuntimeError("VECTOR_DB_API_KEY not set")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")



if not REDIS_TOKEN:
    raise RuntimeError("REDIS_TOKEN not set")



if not WHATSAPP_VERIFY_TOKEN:
    raise RuntimeError("WHATSAPP_VERIFY_TOKEN not set") 
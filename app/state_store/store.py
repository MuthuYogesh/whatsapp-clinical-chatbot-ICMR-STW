import json
from upstash_redis import Redis
from app.config import REDIS_URL, REDIS_TOKEN

# Internal dictionary for fallback if Redis is unavailable
_FALLBACK_STORE = {}

try:
    # Upstash REST client initialization
    r = Redis(url=REDIS_URL, token=REDIS_TOKEN)
    # Ping to check connection
    r.ping()
    REDIS_AVAILABLE = True
    print("✅ Connected to Upstash Redis.")
except Exception as e:
    # Catching generic Exception because upstash_redis raises REST errors,
    # but we keep the logic to fall back to memory
    REDIS_AVAILABLE = False
    print(f"⚠️ Redis unavailable: {e}. Falling back to in-memory state store.")

def get_state(sender_id: str):
    """Retrieves state from Redis or fallback dictionary."""
    if REDIS_AVAILABLE:
        try:
            state_data = r.get(f"state:{sender_id}")
            # upstash_redis returns the value directly (often already a dict or string)
            if state_data:
                return json.loads(state_data) if isinstance(state_data, str) else state_data
            return None
        except Exception:
            pass
    return _FALLBACK_STORE.get(sender_id)

def set_state(sender_id: str, state: dict):
    """Saves state with a 1-hour expiry (TTL) in Redis, or saves to local dict."""
    if REDIS_AVAILABLE:
        try:
            # upstash_redis uses ex=seconds in the set command
            r.set(f"state:{sender_id}", json.dumps(state), ex=3600)
            return
        except Exception as e:
            print(f"Redis Set Error: {e}")
            pass
    _FALLBACK_STORE[sender_id] = state

def clear_state(sender_id: str):
    """Removes state from both Redis and local dict."""
    if REDIS_AVAILABLE:
        try:
            r.delete(f"state:{sender_id}")
        except Exception:
            pass
    if sender_id in _FALLBACK_STORE:
        del _FALLBACK_STORE[sender_id]
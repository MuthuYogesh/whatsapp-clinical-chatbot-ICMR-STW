import time
import asyncio
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.whatsapp.sender import send_whatsapp_message
from app.state_store.store import get_state, set_state
from app.config import LIMIT_DAY, LIMIT_MINUTE

# 1. Define the Key Function
def get_whatsapp_sender_sync(request: Request) -> str:
    """Retrieves phone number from state (populated by middleware)."""
    return getattr(request.state, "sender_phone", get_remote_address(request))

# 2. Initialize the Limiter
limiter = Limiter(key_func=get_whatsapp_sender_sync)

# --- THE STRATEGY ---
# 1. "10/minute": Prevents rapid-fire spamming.
# 2. "25/day": Absolute ceiling.
LIMIT_STRATEGY = f"{LIMIT_MINUTE}; {LIMIT_DAY}"

# 3. Define the Custom Handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handles rate limit breaches with cooldown-aware WhatsApp notifications."""
    sender_id = getattr(request.state, "sender_phone", None)
    
    if sender_id:
        state = get_state(sender_id) or {}
        last_notified = state.get("last_throttle_notification", 0)
        current_time = time.time()

        if current_time - last_notified > 60:
            throttle_msg = (
                "⏳ *Rate Limit Active*\n\n"
                "To ensure clinical accuracy, I process messages one at a time. "
                "Please wait 60 seconds before sending your next query."
            )
            asyncio.create_task(send_whatsapp_message(sender_id, throttle_msg))
            
            state["last_throttle_notification"] = current_time
            set_state(sender_id, state)

    # Note: Using 200 here as per your request to stop Meta's retry loop 
    # while still blocking the local execution.
    return JSONResponse(
        status_code=200,
        content={"error": "Rate limit exceeded"}
    )
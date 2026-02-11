from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.whatsapp.webhook import router as whatsapp_router
from app.whatsapp.webhook import WhatsAppStateMiddleware
from app.whatsapp.sender import send_whatsapp_message
from app.state_store.store import get_state, set_state
import time
import socket
import asyncio


# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)
# Initialize FastAPI app instance
app = FastAPI(title="ICMR STW WhatsApp Demo")

# Attach the limiter to App State
app.state.limiter = limiter

async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handles rate limit breaches without spamming the user.
    Uses a timestamp flag to ensure notifications only happen once per minute.
    """
    sender_id = getattr(request.state, "sender_phone", None)
    
    if sender_id:
        # 1. Check when we last notified this user
        state = get_state(sender_id) or {}
        last_notified = state.get("last_throttle_notification", 0)
        current_time = time.time()

        # 2. Only send if more than 60 seconds have passed since the last warning
        if current_time - last_notified > 60:
            throttle_msg = (
                "⏳ *Rate Limit Active*\n\n"
                "To ensure clinical accuracy, I process messages one at a time. "
                "Please wait 60 seconds before sending your next query."
            )
            
            # Send the message in the background
            asyncio.create_task(send_whatsapp_message(sender_id, throttle_msg))
            
            # Update the state with the new timestamp
            state["last_throttle_notification"] = current_time
            set_state(sender_id, state)

    # 3. CRITICAL: Still return 429 to Meta so they know to stop the retry loop eventually
    return JSONResponse(
        status_code=200,
        content={"error": "Rate limit exceeded"}
    )
# Exception handler for rate limit breaches
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled error and prevents the server from 
    returning a raw stack trace to Meta.
    """
    print(f"🔥 SYSTEM CRASH: {str(exc)}")
    # Returning a 500 tells Meta 'Something is wrong, please stop retrying for a moment'
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error"}
    )
# Register routers (like app.use() in Express)
app.add_middleware(WhatsAppStateMiddleware)  # Add the middleware for state management
app.include_router(whatsapp_router)

# Basic health check endpoint
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "icmr-stw-whatsapp-demo"
    }

# Debug endpoint to check DNS resolution for Facebook API
@app.get("/debug-dns")
def check_dns():
    try:
        # Tries to find the 'address' for the Facebook API
        return {"ip": socket.gethostbyname("graph.facebook.com")}
    except Exception as e:
        return {"error": str(e)}
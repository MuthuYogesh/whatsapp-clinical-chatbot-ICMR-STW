from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter, custom_rate_limit_handler
from app.whatsapp.webhook import router as whatsapp_router
from app.middleware.whatsapp_shield_middleware import WhatsAppShieldMiddleware
from app.core.exceptions import global_exception_handler
import socket


# Initialize FastAPI app instance
app = FastAPI(title="ICMR STW WhatsApp Demo")
# Attach the limiter to App State
app.state.limiter = limiter
# Exception handler for rate limit breaches
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
# Register the global exception handler
app.add_exception_handler(Exception, global_exception_handler)

# Add the middleware for state and Security management
app.add_middleware(WhatsAppShieldMiddleware) 
# Register routers (like app.use() in Express)
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
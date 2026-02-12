import json
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from slowapi.util import get_remote_address
from app.whatsapp.security import verify_whatsapp_signature

class WhatsAppShieldMiddleware(BaseHTTPMiddleware):
    """
    The 'Upgraded' Middleware:
    1. Verifies Meta's digital signature.
    2. Clones the request body (the 'Single Read' fix).
    3. Injects the sender's phone number into request.state.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Applies security checks and state management only to the WhatsApp webhook POST endpoint, 
        ensuring that other routes remain unaffected while providing robust protection against 
        unauthorized access and enabling rate limiting based on sender identity.
        """
        # Apply only to the webhook POST endpoint
        if request.method == "POST" and "/webhook-whatsapp" in request.url.path:
            body_bytes = await request.body()
            signature = request.headers.get("X-Hub-Signature-256")

            # A. Signature Check
            if not verify_whatsapp_signature(body_bytes, signature):
                return Response(content="Unauthorized: Invalid Signature", status_code=401)

            # B. Body Reset (Allows request.json() to be called later)
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive

            # C. State Injection for Rate Limiting
            try:
                payload = json.loads(body_bytes)
                sender = payload['entry'][0]['changes'][0]['value']['messages'][0]['from']
                request.state.sender_phone = str(sender)
            except:
                request.state.sender_phone = get_remote_address(request)
        
        return await call_next(request)
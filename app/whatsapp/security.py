import hmac
import hashlib
from app.config import WHATSAPP_APP_SECRET

def verify_whatsapp_signature(payload: bytes, signature: str) -> bool:
    """
    Validates the X-Hub-Signature-256 header sent by Meta.
    """
    if not signature:
        return False
    
    # Remove 'sha256=' prefix if present
    clean_signature = signature.replace("sha256=", "") if "sha256=" in signature else signature

    # Calculate expected signature
    expected_signature = hmac.new(
        key=WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, clean_signature)
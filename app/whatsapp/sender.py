import httpx # Use httpx for async
import socket
from app.config import WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_TOKEN

BASE_URL = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

async def send_whatsapp_message(to: str, text: str):
    """Asynchronously sends a WhatsApp message."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, json=payload)
        if not response.is_success:
            print(f"WhatsApp Error: {response.text}")
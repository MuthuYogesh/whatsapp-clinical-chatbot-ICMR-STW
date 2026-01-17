import httpx
from app.config import WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_TOKEN

BASE_URL = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
HEADERS = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}

async def send_whatsapp_message(to: str, text: str):
    """Sends a standard text message."""
    payload = {
        "messaging_product": "whatsapp", "to": to, "type": "text",
        "text": {"body": text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(BASE_URL, headers=HEADERS, json=payload)

async def send_interactive_buttons(to: str, header: str, body: str, buttons: list):
    """Sends a message with up to 3 interactive quick-reply buttons."""
    button_objs = []
    for btn in buttons:
        button_objs.append({
            "type": "reply",
            "reply": {"id": btn["id"], "title": btn["title"]}
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {"buttons": button_objs}
        }
    }
    async with httpx.AsyncClient() as client:
        await client.post(BASE_URL, headers=HEADERS, json=payload)
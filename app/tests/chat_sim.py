import asyncio
import uuid
from unittest.mock import AsyncMock, patch
from app.whatsapp.webhook import medical_orchestrator
from app.state_store.store import clear_state

async def mock_send_message(recipient_id, message_text):
    """
    Replaces the WhatsApp API call with a simple print statement.
    """
    print(f"\n[BOT]: {message_text}")

async def run_simulation():
    # Use a consistent session ID for the simulation
    session_id = f"sim_{uuid.uuid4().hex[:8]}"
    clear_state(session_id)
    
    print("🏥 Clinical Assistant Chat Simulation")
    print("Type '/start' to reset or 'exit' to quit.\n")

    # Patch the sender so it prints to console instead of calling Meta's API
    with patch("app.whatsapp.webhook.send_whatsapp_message", side_effect=mock_send_message):
        while True:
            try:
                user_input = input("[YOU]: ")
                
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Exiting simulation.")
                    break
                
                if not user_input.strip():
                    continue

                # Pass the input to your actual production orchestrator
                await medical_orchestrator(session_id, user_input)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n[ERROR]: {e}")

if __name__ == "__main__":
    asyncio.run(run_simulation())
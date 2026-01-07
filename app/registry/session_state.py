from typing import Dict

# Very small in-memory session store mapping chat_id -> stw_id
_sessions: Dict[str, str] = {}

def set_active_stw(chat_id: str, stw_id: str):
    _sessions[chat_id] = stw_id

def get_active_stw(chat_id: str) -> str | None:
    return _sessions.get(chat_id)

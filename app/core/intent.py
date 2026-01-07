def detect_intent(text: str) -> str:
    text_l = text.lower()
    if any(w in text_l for w in ["yes", "no", "true", "false"]):
        return "verification"
    return "question"

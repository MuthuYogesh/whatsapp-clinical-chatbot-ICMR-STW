class LLMClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def call(self, prompt: str) -> str:
        # Placeholder LLM call
        return "LLM response: (stub)"

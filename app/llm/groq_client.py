import json
from typing import Union
from groq import AsyncGroq # Switched to Async
from app.config import GROQ_API_KEY

# Initialize Async client
client = AsyncGroq(api_key=GROQ_API_KEY)

async def call_groq(
    messages: list, 
    model: str = "llama-3.1-8b-instant", 
    temperature: float = 0, 
    max_tokens: int = 500,
    response_format: str = "text"
) -> Union[str, dict, None]:
    """
    Asynchronous Groq API caller.
    """
    try:
        # Use 'await' to prevent blocking other users
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": response_format}
        )
        
        raw_content = response.choices[0].message.content.strip()
        
        if response_format == "json_object":
            return json.loads(raw_content)
        
        return raw_content
        
    except Exception as e:
        print(f"Groq API Error: {e}")
        return None
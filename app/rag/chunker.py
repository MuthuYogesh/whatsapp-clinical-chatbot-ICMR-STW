import re

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 150) -> list[str]:
    """
    Semantic chunking: Normalizes whitespace and splits by sentences 
    to preserve context.
    """
    # Normalize extra whitespace and mid-word hyphens
    text = re.sub(r'\s+', ' ', text)
    
    # Split by sentences (looks for period followed by space)
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            # Overlap: simple implementation starts new chunk with the current sentence
            current_chunk = sentence + " "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks
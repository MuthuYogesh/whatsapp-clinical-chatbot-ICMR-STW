import fitz  # PyMuPDF
from pathlib import Path

def load_pdf_text(pdf_path: str) -> str:
    """
    Extracts text from PDF by blocks to maintain structural integrity 
    of columns and flowcharts.
    """
    doc = fitz.open(pdf_path)
    full_text = []

    for page in doc:
        # Get text blocks to preserve reading order of columns
        blocks = page.get_text("blocks")
        # Sort blocks: Primary sort by vertical position (y1), 
        # Secondary sort by horizontal (x0)
        blocks.sort(key=lambda b: (b[1], b[0])) 
        
        for b in blocks:
            # block[4] contains the actual text
            clean_line = b[4].replace("\n", " ").strip()
            if clean_line:
                full_text.append(clean_line)

    return "\n".join(full_text)
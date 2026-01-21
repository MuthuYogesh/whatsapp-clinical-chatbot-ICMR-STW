import fitz  # PyMuPDF
import re
from typing import List, Dict

def load_pdf_with_metadata(pdf_path: str) -> List[Dict]:
    """
    Extracts text from PDF by blocks while preserving page numbers and 
    detecting potential STW titles from headers.
    
    Returns:
        List[Dict]: A list of dictionaries containing 'page_number', 'stw_title', and 'text'.
    """
    doc = fitz.open(pdf_path)
    pages_data = []

    for page_num, page in enumerate(doc, start=1):
        # Get text blocks to preserve reading order of columns
        blocks = page.get_text("blocks")
        # Sort blocks: Primary sort by vertical position (y1), 
        # Secondary sort by horizontal (x0) to handle multi-column clinical tables
        blocks.sort(key=lambda b: (b[1], b[0])) 
        
        page_text_lines = []
        for b in blocks:
            # block[4] is the text content
            clean_line = b[4].replace("\n", " ").strip()
            if clean_line:
                page_text_lines.append(clean_line)

        # Join the text for the current page
        page_content = "\n".join(page_text_lines)
        
        # --- STW Title Detection Logic ---
        # We assume the first significant line of a page is often the STW title or header.
        # We clean it to be used in a REF_ID (remove spaces/special chars)
        stw_title = "General_Guideline"
        if page_text_lines:
            # Look at the first 2 lines to find a valid title, skipping common noise
            for line in page_text_lines[:2]:
                if len(line) > 3 and not line.isdigit():
                    # Clean the title: Replace spaces/slashes with underscores
                    stw_title = re.sub(r'[^a-zA-Z0-9]', '_', line).strip('_')
                    break

        pages_data.append({
            "page_number": page_num,
            "stw_title": stw_title,
            "text": page_content
        })

    doc.close()
    return pages_data
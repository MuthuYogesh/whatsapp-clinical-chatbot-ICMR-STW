from app.rag.loader import load_pdf_text

pdf_path = "data/stw/peds_acute_encephalitis_syndrome.pdf"

text = load_pdf_text(pdf_path)

print("===== FIRST 2000 CHARACTERS =====")
print(text[:2000])

print("\n===== LAST 2000 CHARACTERS =====")
print(text[-2000:])

print("\nTOTAL CHARACTERS:", len(text))

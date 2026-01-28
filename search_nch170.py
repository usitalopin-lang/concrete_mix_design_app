from pypdf import PdfReader
import re

def search_nch170_tables(path):
    reader = PdfReader(path)
    text_matches = []
    
    keywords = ["Tabla 4", "Tabla 5", "Durabilidad", "dosis de cemento", "razón agua/cemento"]
    
    print(f"Searching {len(reader.pages)} pages...")
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        for kw in keywords:
            if kw in text:
                # Extract a snippet around the keyword
                start = max(0, text.find(kw) - 100)
                end = min(len(text), text.find(kw) + 500)
                snippet = text[start:end].replace('\n', ' ')
                text_matches.append(f"Page {i+1} ({kw}): {snippet}...")
                
    return "\n".join(text_matches)

try:
    path = r"C:\Users\cridiaz\Downloads\Documentos\NCH 170.pdf"
    results = search_nch170_tables(path)
    print("--- NCh 170 Search Results ---")
    print(results[:2000]) # Limit output
except Exception as e:
    print(f"Error: {e}")

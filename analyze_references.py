import pandas as pd
from pypdf import PdfReader
import os

# Paths provided by user
doc_analysis_path = r"C:\Users\cridiaz\Downloads\Documentos\c71a5620-7ac8-4d53-9110-ea4d9c084e3a.pdf"
nch170_path = r"C:\Users\cridiaz\Downloads\Documentos\NCH 170.pdf"
excel1_path = r"C:\Users\cridiaz\Downloads\HojasDeCalculo\Mixture-proportioning-2021-06 (2).xlsx"
excel2_path = r"C:\Users\cridiaz\Downloads\HojasDeCalculo\INF-DOH-1841_G30.xlsx"

output_file = "reference_analysis.txt"

def analyze_pdf(path, max_pages=None):
    results = [f"--- Analyzing PDF: {os.path.basename(path)} ---"]
    try:
        reader = PdfReader(path)
        number_of_pages = len(reader.pages)
        results.append(f"Total Pages: {number_of_pages}")
        
        pages_to_read = min(number_of_pages, max_pages) if max_pages else number_of_pages
        
        text_content = ""
        for i in range(pages_to_read):
            page = reader.pages[i]
            text = page.extract_text()
            text_content += f"\n--- Page {i+1} ---\n{text}\n"
            
        results.append(text_content)
    except Exception as e:
        results.append(f"Error reading PDF: {e}")
    return "\n".join(results)

def analyze_excel(path):
    results = [f"--- Analyzing Excel: {os.path.basename(path)} ---"]
    try:
        xl = pd.ExcelFile(path)
        results.append(f"Sheet Names: {xl.sheet_names}")
        
        # Read first sheet sample
        if xl.sheet_names:
            first_sheet = xl.sheet_names[0]
            df = pd.read_excel(path, sheet_name=first_sheet, nrows=10)
            results.append(f"\nSample Data from sheet '{first_sheet}':")
            results.append(df.to_string())
            
            # Read second sheet if exists (often relevant data is not in cover)
            if len(xl.sheet_names) > 1:
                second_sheet = xl.sheet_names[1]
                df2 = pd.read_excel(path, sheet_name=second_sheet, nrows=10)
                results.append(f"\nSample Data from sheet '{second_sheet}':")
                results.append(df2.to_string())

    except Exception as e:
        results.append(f"Error reading Excel: {e}")
    return "\n".join(results)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("REFERENCE DOCUMENTS ANALYSIS\n============================\n\n")
    
    # 1. Analyze the 'Analysis' PDF (Small, read all)
    f.write(analyze_pdf(doc_analysis_path) + "\n\n")
    
    # 2. Analyze NCh 170 (Large, read first 5 pages/TOC)
    f.write(analyze_pdf(nch170_path, max_pages=5) + "\n\n")
    
    # 3. Analyze Excel 1
    f.write(analyze_excel(excel1_path) + "\n\n")
    
    # 4. Analyze Excel 2
    f.write(analyze_excel(excel2_path) + "\n\n")

print(f"Analysis complete. Results written to {output_file}")

import pdfplumber
import os


def extract_text_from_pdf(file_path):
    extracted_text = ""

    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"[PDF Reader] Opened PDF with {total_pages} page(s).")

            
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n\n"
                    print(f"[PDF Reader] Extracted text from page {i + 1}.")
                else:
                    print(f"[PDF Reader] No text found on page {i + 1} (may be image-based).")

      
        if not extracted_text.strip():
            return "[PDF Reader] No readable text found in the PDF. The document may be image-based or scanned."

        return extracted_text.strip()

    except FileNotFoundError:
        return f"[PDF Reader Error] File not found: {file_path}"
    except Exception as e:
        return f"[PDF Reader Error] Failed to extract text: {str(e)}"


def extract_tables_from_pdf(file_path):
    all_tables = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        all_tables.append(table)
                    print(f"[PDF Reader] Found {len(tables)} table(s) on page {i + 1}.")

        return all_tables

    except Exception as e:
        print(f"[PDF Reader Error] Table extraction failed: {str(e)}")
        return []
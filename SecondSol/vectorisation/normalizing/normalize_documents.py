import os
import json
import fitz  # PyMuPDF
import re

CORPUS_DIR = "corpus"
JSON_SCRAPES_DIR = os.path.join(CORPUS_DIR, "json_scrapes")
PDF_SCRAPES_DIR = os.path.join(CORPUS_DIR, "pdf_scrapes")
PDF_MANUAL_DIR = os.path.join(CORPUS_DIR, "pdf_ajoutes_manuellement")
OUTPUT_FILE = os.path.join(CORPUS_DIR, "normalized/all_docs_normalized.jsonl")

def clean_text(text):
    # Remove non-printable/control characters except common whitespace
    cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)
    return cleaned

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        print(f"Failed to extract PDF text from {pdf_path}: {e}")
        return None

def normalize_pdf_file(path, specialty=None):
    text = extract_text_from_pdf(path)
    if not text:
        return None
    clean = clean_text(text)
    return {
        "source": path,
        "specialty": specialty if specialty else "NA",
        "content": clean,
    }


def load_json_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load JSON {filepath}: {e}")
        return None

def load_text_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to load text {filepath}: {e}")
        return None

def normalize_json_scrape(doc, filename):
    # Assuming doc is a dict from your example
    return {
        "source": "json_scrape",
        "url": doc.get("url", None),
        "file_name": filename,
        "specialty": doc.get("filierespecifique", "None"),
        "title": doc.get("title", ""),
        "content": doc.get("content", ""),
        "metadata": {
            "site": doc.get("site", ""),
            "category": doc.get("category", ""),
            "datespecifique": doc.get("datespecifique", "")
        }
    }

def normalize_pdf_scrape(filepath, specialty=None):
    # For pdf scrapes, assume either JSON or plain text with same name
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".json":
        doc = load_json_file(filepath)
        if not doc:
            return None
        content = doc.get("text_content") or doc.get("content") or ""
        title = doc.get("title", filename)
        url = doc.get("url", None)
        metadata = doc.get("metadata", {})
    else:
        # plain text
        content = load_text_file(filepath)
        title = filename
        url = None
        metadata = {}

    return {
        "source": "pdf_scrape",
        "url": url,
        "file_name": filename,
        "specialty": specialty or "None",
        "title": title,
        "content": content,
        "metadata": metadata
    }

def normalize_pdf_manual(filepath, specialty=None):
    # same logic as pdf_scrape for now, just different source tag
    normalized = normalize_pdf_scrape(filepath, specialty)
    if normalized:
        normalized["source"] = "pdf_manual"
    return normalized

def main():
    print("Starting document normalization...")
    all_docs = []

    print("Loading JSON scrapes...")
    for file in os.listdir(JSON_SCRAPES_DIR):
        if file.endswith(".json"):
            path = os.path.join(JSON_SCRAPES_DIR, file)
            doc = load_json_file(path)
            if doc:
                normalized = normalize_json_scrape(doc, file)
                all_docs.append(normalized)

    print("Loading PDF scrapes...")
    for root, dirs, files in os.walk(PDF_SCRAPES_DIR):
        parts = os.path.relpath(root, PDF_SCRAPES_DIR).split(os.sep)
        specialty = parts[0] if parts and parts[0] != '.' else None
        for file in files:
            path = os.path.join(root, file)
            if file.endswith((".json", ".txt")):
                normalized = normalize_pdf_scrape(path, specialty)
                if normalized:
                    all_docs.append(normalized)
            elif file.endswith(".pdf"):
                normalized = normalize_pdf_file(path, specialty)
                if normalized:
                    all_docs.append(normalized)

    print("Loading manual PDFs...")
    for root, dirs, files in os.walk(PDF_MANUAL_DIR):
        parts = os.path.relpath(root, PDF_MANUAL_DIR).split(os.sep)
        specialty = parts[0] if parts and parts[0] != '.' else None
        for file in files:
            path = os.path.join(root, file)
            if file.endswith((".json", ".txt")):
                normalized = normalize_pdf_manual(path, specialty)
                if normalized:
                    all_docs.append(normalized)
            elif file.endswith(".pdf"):
                normalized = normalize_pdf_file(path, specialty)
                if normalized:
                    all_docs.append(normalized)

    print(f"Saving {len(all_docs)} documents to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for doc in all_docs:
            f_out.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print("Done.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exception occurred:", e)











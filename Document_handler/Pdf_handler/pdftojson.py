import os
import json
import fitz  # PyMuPDF
import re
from pathlib import Path

DOCUMENT_HANDLER_DIR = Path(__file__).parent.parent
CORPUS_DIR = DOCUMENT_HANDLER_DIR / "Corpus"
SCRAPPING_DIR = DOCUMENT_HANDLER_DIR / "scraping"

INPUT_DIRS = {
    "pdf_manual": CORPUS_DIR / "pdf_man",
    #"pdf_scraped": CORPUS_DIR / "pdf_scrap"
}

OUTPUT_DIR = CORPUS_DIR / "json_Output_pdf&Scrap"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text):
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u00A0-\uFFFF]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_text_lines(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text("text") for page in doc])
        return [line.strip() for line in text.splitlines() if line.strip()]
    except Exception as e:
        print(f"❌ Erreur PDF {pdf_path}: {e}")
        return []

def guess_title(lines):
    for line in lines[:10]:
        if len(line) > 10:
            return line
    return "Titre inconnu"

def guess_authors(lines):
    pattern = re.compile(r"(auteur|author|réalisé par|nom|par)[^\n:]*[:\-]?\s*(.*)", re.IGNORECASE)
    for line in lines:
        match = pattern.search(line)
        if match:
            possible_names = match.group(2)
            names = re.split(r"[;,/]| et ", possible_names)
            return [name.strip() for name in names if name.strip()]
    return []

def guess_date(lines):
    date_patterns = [
        r"\b(\d{2}/\d{2}/\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{2}\.\d{2}\.\d{4})\b",
        r"\b(\d{4})\b"
    ]
    for line in lines[:20]:
        for pat in date_patterns:
            match = re.search(pat, line)
            if match:
                return match.group(1)
    return None

def process_pdf_file(file_path, source_key, specialty="NA"):
    lines = extract_text_lines(file_path)
    if not lines:
        return None

    full_text = "\n".join(lines)
    doc_json = {
        "source": source_key,
        "file_name": os.path.basename(file_path),
        "pdf_path": os.path.abspath(file_path),
        "specialty": specialty,
        "content": clean_text(full_text),
        "metadata": {
            "title": guess_title(lines),
            "auteurs": guess_authors(lines),
            "date": guess_date(lines)
        }
    }
    return doc_json

def augment_with_scraped_metadata(doc, pdf_path):
    """
    TODO: Enhance the document JSON with additional metadata from scraping.
    For example, if a file 'my_doc.pdf' exists, we might look for:
    - 'my_doc.json' in the same folder (sidecar metadata)
    - or use a database / pre-parsed metadata file.
    
    Example expected metadata fields:
      - url: original web page
      - scrape_date: date of collection
      - tags: list of tags/categories

    For now, this is a placeholder.
    """
    # Stub logic — customize this based on how scraped metadata is stored
    metadata_path = os.path.splitext(pdf_path)[0] + ".meta.json"
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                scraped_meta = json.load(f)
            # Merge safely
            doc["metadata"].update(scraped_meta)
        except Exception as e:
            print(f"⚠️ Erreur lecture metadata pour {pdf_path}: {e}")
    else:
        print(f"ℹ️ Aucun fichier de metadata pour {pdf_path}")


def run():
    count = 0
    for source_key, input_dir in INPUT_DIRS.items():
        for root, dirs, files in os.walk(input_dir):
            specialty = os.path.relpath(root, input_dir).split(os.sep)[0]
            for file in files:
                if file.lower().endswith(".pdf"):
                    full_path = os.path.join(root, file)
                    print(f"⏳ Traitement : {file} ({source_key})")
                    doc = process_pdf_file(full_path, source_key, specialty)
                    if doc:
                        output_filename = os.path.splitext(file)[0] + ".json"
                        output_path = os.path.join(OUTPUT_DIR, output_filename)
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(doc, f, ensure_ascii=False, indent=2)
                        count += 1
    # TODO augment_with_scraped_metadata
    #if doc:
    #    if source_key == "pdf_scraped":
    #        augment_with_scraped_metadata(doc, full_path)

    print(f"\n✅ {count} fichiers JSON générés dans : {OUTPUT_DIR}")

if __name__ == "__main__":
    print("🔄 Démarrage du traitement des PDF...")
    run()

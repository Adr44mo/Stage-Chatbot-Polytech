import os
import json
import fitz
import re
from pathlib import Path

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

def _process_pdf_common(pdf_path):
    lines = extract_text_lines(pdf_path)
    if not lines:
        return None
    full_text = "\n".join(lines)
    file_name = os.path.basename(pdf_path)
    return lines, full_text, file_name

def process_manual_pdf_file(pdf_path):
    """
    Traite un PDF manuel à partir de son chemin et retourne un dictionnaire JSON.
    """
    pdf_path = Path(pdf_path)
    # On suppose que la spécialité est le sous-dossier juste sous pdf_man
    try:
        speciality = pdf_path.relative_to(pdf_path.parents[2]).parts[0]
    except Exception:
        speciality = "NA"
    result = _process_pdf_common(pdf_path)
    if not result:
        return None
    lines, full_text, file_name = result

    doc_json = {
        "source": "pdf_manual",
        "file_name": file_name,
        "pdf_path": str(pdf_path),
        "speciality": speciality,
        "content": clean_text(full_text),
        "metadata": {
            "title": guess_title(lines),
            "auteurs": guess_authors(lines),
            "date": guess_date(lines)
        }
    }
    return doc_json

def process_scraped_pdf_file(pdf_path):
    """
    Traite un PDF scraping à partir de son chemin et retourne un dictionnaire JSON.
    """
    pdf_path = Path(pdf_path)
    # On suppose que le site est le dossier parent de pdf_scrapes
    try:
        site_name = pdf_path.parents[2].name
    except Exception:
        site_name = "unknown_site"
    # On suppose que la spécialité est le sous-dossier juste sous pdf_scrapes
    try:
        speciality = pdf_path.relative_to(pdf_path.parents[1]).parts[0]
    except Exception:
        speciality = "NA"
    # Cherche un éventuel pdf_map.json dans le dossier parent de pdf_scrapes
    pdf_metadata_map = {}
    map_path = pdf_path.parents[1].parent / "pdf_map.json"
    if map_path.exists():
        try:
            with open(map_path, "r", encoding="utf-8") as f:
                pdf_metadata_map = json.load(f)
        except Exception as e:
            print(f"⚠️ Erreur lecture de {map_path}: {e}")

    result = _process_pdf_common(pdf_path)
    if not result:
        return None
    lines, full_text, file_name = result

    doc_json = {
        "source": site_name,
        "file_name": file_name,
        "pdf_path": str(pdf_path),
        "speciality": speciality,
        "content": clean_text(full_text),
        "metadata": {
            "title": guess_title(lines),
            "auteurs": guess_authors(lines),
            "date": guess_date(lines)
        }
    }
    # Ajoute des métadonnées spécifiques si présentes
    if pdf_metadata_map and file_name in pdf_metadata_map:
        doc_json["metadata"].update(pdf_metadata_map[file_name])
    return doc_json
import os
import json
import fitz  # PyMuPDF
import re
from pathlib import Path

# Setup paths
DOCUMENT_HANDLER_DIR = Path(__file__).parent.parent
CORPUS_DIR = DOCUMENT_HANDLER_DIR / "Corpus"

INPUT_DIRS = {
    "pdf_manual": CORPUS_DIR / "pdf_man",
    
    "scraped_geipi": CORPUS_DIR / "data_sites" / "geipi_polytech" / "pdf_scrapes",
    "scraped_reseau": CORPUS_DIR / "data_sites" / "polytech_réseau" / "pdf_scrapes",
    "scraped_sorbonne": CORPUS_DIR / "data_sites" / "polytech_sorbonne" / "pdf_scrapes"
}

OUTPUT_DIR = CORPUS_DIR / "json_Output_pdf&Scrap"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Text extraction and cleaning ---

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

# --- Metadata guessing ---

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

# --- PDF processor ---

def process_pdf_file(file_path, source_key, specialty="NA", extra_metadata=None):
    lines = extract_text_lines(file_path)
    if not lines:
        print(f"❌ Aucun JSON généré pour : {file_path} (process_pdf_file a retourné None)")
                    
        return None

    full_text = "\n".join(lines)
    file_name = os.path.basename(file_path)

    doc_json = {
        "source": source_key,
        "file_name": file_name,
        "pdf_path": str(file_path),
        "specialty": specialty,
        "content": clean_text(full_text),
        "metadata": {
            "title": guess_title(lines),
            "auteurs": guess_authors(lines),
            "date": guess_date(lines)
        }
    }

    if extra_metadata and file_name in extra_metadata:
        doc_json["metadata"].update(extra_metadata[file_name])

    return doc_json

# --- Output directory management ---

def clean_output_dir(input_dirs, output_dir=OUTPUT_DIR):
    """Supprime les fichiers JSON du output_dir qui ne correspondent à aucun PDF dans input_dirs."""
    # Récupère tous les PDF attendus
    expected_jsons = set()
    for input_dir in input_dirs.values():
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith(".pdf"):
                    json_name = os.path.splitext(file)[0] + ".json"
                    expected_jsons.add(json_name)
    # Supprime les JSON orphelins
    for json_file in output_dir.glob("*.json"):
        if json_file.name not in expected_jsons:
            print(f"🗑️ Suppression du fichier orphelin : {json_file.name}")
            json_file.unlink()

# ...existing code...

def run_for_input_dirs(input_dirs, output_dir=OUTPUT_DIR):
    """
    Traite tous les PDF pour un dictionnaire input_dirs {source_key: dossier}
    et génère les fichiers JSON correspondants dans output_dir.
    """
    clean_output_dir(input_dirs, output_dir)
    count = 0

    for source_key, input_dir in input_dirs.items():
        is_scraped = source_key.startswith("scraped_")
        pdf_metadata_map = {}

        if is_scraped:
            map_path = input_dir.parent / "pdf_map.json"
            print(f"🔍 Chargement des métadonnées pour {source_key} depuis {map_path}")
            if map_path.exists():
                try:
                    with open(map_path, "r", encoding="utf-8") as f:
                        pdf_metadata_map = json.load(f)
                except Exception as e:
                    print(f"⚠️ Erreur lecture de {map_path}: {e}")
            else:
                print(f"ℹ️ Aucun fichier pdf_map.json trouvé pour {source_key}")

        for root, _, files in os.walk(input_dir):
            specialty = Path(root).relative_to(input_dir).parts[0] if root != str(input_dir) else "NA"
            for file in files:
                if file.lower().endswith(".pdf"):
                    full_path = os.path.join(root, file)
                    output_filename = os.path.splitext(file)[0] + ".json"
                    output_path = output_dir / output_filename

                    pdf_mtime = os.path.getmtime(full_path)
                    json_mtime = output_path.stat().st_mtime if output_path.exists() else 0

                    # Vérifie d'abord si le PDF doit être traité (modification, nouveau pdf...)
                    if not output_path.exists() or pdf_mtime > json_mtime:
                        print(f"⏳ Traitement : {file} ({source_key})")
                        doc = process_pdf_file(
                            full_path,
                            source_key,
                            specialty=specialty,
                            extra_metadata=pdf_metadata_map if is_scraped else None
                        )
                        if doc:
                            if output_path.exists():
                                print(f"♻️ Fichier écrasé : {output_filename}")
                            else:
                                print(f"🆕 Nouveau fichier créé : {output_filename}")
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(doc, f, ensure_ascii=False, indent=2)
                            count += 1
                    else:
                        print(f"⏩ Inchangé, non traité : {output_filename}")

    print(f"\n✅ {count} fichiers JSON générés dans : {output_dir}")


# --- Main execution logic ---

def run():
    clean_output_dir(INPUT_DIRS, OUTPUT_DIR)
    count = 0

    for source_key, input_dir in INPUT_DIRS.items():
        is_scraped = source_key.startswith("scraped_")
        pdf_metadata_map = {}

    
        if is_scraped:
            # 🔍 Load map one level up from pdf_scrapes
            map_path = input_dir.parent / "pdf_map.json"
            print(f"🔍 Chargement des métadonnées pour {source_key} depuis {map_path}")
            if map_path.exists():
                try:
                    with open(map_path, "r", encoding="utf-8") as f:
                        pdf_metadata_map = json.load(f)
                except Exception as e:
                    print(f"⚠️ Erreur lecture de {map_path}: {e}")
            else:
                print(f"ℹ️ Aucun fichier pdf_map.json trouvé pour {source_key}")

        # Traverse PDFs
        for root, _, files in os.walk(input_dir):
            specialty = Path(root).relative_to(input_dir).parts[0] if root != str(input_dir) else "NA"
            for file in files:
                if file.lower().endswith(".pdf"):
                    full_path = os.path.join(root, file)
                    output_filename = os.path.splitext(file)[0] + ".json"
                    output_path = OUTPUT_DIR / output_filename

                    pdf_mtime = os.path.getmtime(full_path)
                    json_mtime = output_path.stat().st_mtime if output_path.exists() else 0

                    # Vérifie d'abord si le PDF doit être traité (modification, nouveau pdf...)
                    if not output_path.exists() or pdf_mtime > json_mtime:
                        print(f"⏳ Traitement : {file} ({source_key})")
                        doc = process_pdf_file(
                            full_path,
                            source_key,
                            specialty=specialty,
                            extra_metadata=pdf_metadata_map if is_scraped else None
                        )
                        if doc:
                            if output_path.exists():
                                print(f"♻️ Fichier écrasé : {output_filename}")
                            else:
                                print(f"🆕 Nouveau fichier créé : {output_filename}")
                            with open(output_path, "w", encoding="utf-8") as f:
                                json.dump(doc, f, ensure_ascii=False, indent=2)
                            count += 1
                    else:
                        print(f"⏩ Inchangé, non traité : {output_filename}")

    print(f"\n✅ {count} fichiers JSON générés dans : {OUTPUT_DIR}")

# --- Entry point ---
if __name__ == "__main__":
    print("🔄 Démarrage du traitement des PDF...")
    run()

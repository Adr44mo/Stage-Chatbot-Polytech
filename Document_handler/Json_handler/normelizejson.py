import json
from pathlib import Path
from datetime import datetime

DOCUMENT_HANDLER_DIR = Path(__file__).parent.parent
CORPUS_DIR = DOCUMENT_HANDLER_DIR / "Corpus"
SCRAPPING_DIR = DOCUMENT_HANDLER_DIR / "scraping"

INPUT_DIRS = {
    "scraped_geipi": SCRAPPING_DIR / "data_sites" / "geipi_polytech" / "json_scrapes",
    "scraped_reseau": SCRAPPING_DIR / "data_sites" / "polytech_réseau" / "json_scrapes",
    "scraped_sorbonne": SCRAPPING_DIR / "data_sites" / "polytech_sorbonne" / "json_scrapes"
}

OUTPUT_VALIDATED_DIR = CORPUS_DIR / "json_normalized" / "validated"
OUTPUT_VALIDATED_DIR.mkdir(parents=True, exist_ok=True)

def normalize_entry(raw_entry: dict, chemin_local: str, site_name: str) -> dict:
    """
    Transforme une entrée brute de scraping en format JSON normalisé.
    """
    return {
        "document_type": "page_web",  # par défaut
        "metadata": {
            "title": raw_entry.get("title", "Sans titre")
        },
        "source": {
            "category": "scrapping",
            "chemin_local": chemin_local,
            "url": raw_entry.get("url"),
            "site": raw_entry.get("site", site_name)
        },
        "content": raw_entry.get("content", ""),
        "tags": [],  # vide pour l’instant
        "type_specific": {},  # rien de spécifique pour page_web
    }

def normalize_all(input_dirs=None):
    """
    Normalise les fichiers JSON des dossiers spécifiés dans input_dirs.
    - input_dirs : dict {nom_source: Path_vers_dossier}
      Si None, utilise INPUT_DIRS par défaut.
    """
    total = 0
    if input_dirs is None:
        input_dirs = INPUT_DIRS

    for source_key, input_dir in input_dirs.items():
        print(f"📂 Traitement du dossier : {input_dir}")
        site_name = source_key.replace("scraped_", "")
        for json_file in input_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                # Cas où c’est une liste d’entrées
                if isinstance(raw_data, list):
                    entries = raw_data
                else:
                    entries = [raw_data]

                for i, entry in enumerate(entries):
                    normalized = normalize_entry(entry, chemin_local=str(json_file), site_name=site_name)
                    # Nom de fichier : <site>_<hash>.json ou fallback
                    name = entry.get("hash", f"{json_file.stem}_{i}")
                    out_path = OUTPUT_VALIDATED_DIR / f"{site_name}_{name}.json"
                    with open(out_path, "w", encoding="utf-8") as f_out:
                        json.dump(normalized, f_out, ensure_ascii=False, indent=2)
                    total += 1

            except Exception as e:
                print(f"⚠️ Erreur traitement de {json_file}: {e}")

    print(f"\n✅ {total} fichiers normalisés sauvegardés dans : {OUTPUT_VALIDATED_DIR}")

if __name__ == "__main__":
    normalize_all(INPUT_DIRS)

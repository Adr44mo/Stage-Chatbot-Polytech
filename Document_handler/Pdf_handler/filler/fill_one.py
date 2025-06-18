import json
import os
import time
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.ollama_wrapper import ask_model
from jsonschema import validate, ValidationError
from fill_logic import route_document


INPUT_DIR = Path(__file__).parent.parent.parent / "Corpus" / "json_Output_pdf&Scrap"
VALID_DIR = Path(__file__).parent.parent.parent / "Corpus" / "json_normalized" / "validated"
PROCESSED_DIR = Path(__file__).parent.parent.parent / "Corpus" / "json_normalized" / "processed"
SCHEMA_PATH = Path(__file__).parent / "schema" / "polytech_schema.json"

VALID_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

with open(SCHEMA_PATH, encoding="utf-8") as f:
    SCHEMA = json.load(f)

def validate_with_schema(data):
    try:
        validate(instance=data, schema=SCHEMA)
        return True
    except ValidationError as e:
        print(f"[❌ Validation error] {e.message}")
        return False


def process_file(file_path: Path, index: int, total: int):
    print(f"[📄 {index+1}/{total}] Traitement de {file_path.name}")
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        updated = route_document(data)
        out_path = VALID_DIR / file_path.name if validate_with_schema(updated) else PROCESSED_DIR / file_path.name
        out_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False), encoding="utf-8")
        if out_path.exists():
            print(f"[✅] Fichier traité : {out_path.name} (chemin: {out_path})")
        else:
            print(f"[❌] Fichier non créé : {out_path.name} (chemin: {out_path})")
    except Exception as e:
        print(f"[⚠️ Erreur sur {file_path.name}] {e}")
        traceback.print_exc()

def main():
    files = list(INPUT_DIR.glob("*.json"))
    total = len(files)
    if total == 0:
        print("Aucun fichier à traiter.")
        return

    cpu_cores = os.cpu_count() or 2
    max_workers = min(cpu_cores - 1, total)
    print(f"[⚙️] Lancement avec {max_workers} workers sur {total} fichiers")

    start = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_file, f, i, total)
            for i, f in enumerate(files)
        ]
        for future in as_completed(futures):
            future.result()

    duration = time.time() - start
    print(f"\n⏱️ Traitement terminé en {duration:.2f} secondes pour {total} fichiers.")

if __name__ == "__main__":
    main()

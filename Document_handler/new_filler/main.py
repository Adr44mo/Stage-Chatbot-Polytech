from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os

from .config import INPUT_DIR, VECT_MAPS, VALID_DIR, PROCESSED_DIR, INPUT_MAPS
from .graph.build_graph import build_graph
from .preprocessing import build_map, update_map

def organize_files():
    """Organiser les fichiers en mettant les anciens fichiers validées dans le dossier 'processed'."""
    if not PROCESSED_DIR.exists():
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    for file in VALID_DIR.glob("*.json"):
        if file.is_file():
            new_path = PROCESSED_DIR / file.name
            file.rename(new_path)
            print(f"Déplacé {file} vers {new_path}")

def already_processed(file_path):
    """Vérifier si le fichier a déjà été traité et s'il a été copier du dossier 'processed' vers le dossier 'validated'."""
    filename = Path(file_path).stem
    for processed_file in PROCESSED_DIR.glob(f"{filename}.*"):
        if processed_file.is_file():
            dest = VALID_DIR / processed_file.name
            processed_file.rename(dest)
            print(f"Déplacé {processed_file} vers {dest}")
            return True
    return False

def Check_vect_maps_files_are_processed():
    """Vérifier si tous les fichiers dans VECT_MAPS ont été traités."""
    for vect_map in INPUT_MAPS.glob("*.json"):
        with open(vect_map, 'r', encoding="utf-8") as f:
            vect_map_data = json.load(f)
        for entry in vect_map_data.values():
            if not already_processed(file_path=entry["path"]):
                print(f"[⚠️] Fichier non traité trouvé : {entry["path"]}")
                return False
    print("[✅] Tous les fichiers INPUT_MAPS ont été traités.")
    return True

def run_preprocessing():
    build_map.input_maps()
    build_map.output_maps()
    update_map.update_input_maps()
    organize_files()

def run_pipeline(file_path, hash):
    graph = build_graph()
    state = {"file_path": str(file_path), "hash": hash}
    graph.invoke(state)

def save_progress(done, total, path="progress.json"):
    with open(path, "w") as f:
        json.dump({"done": done, "total": total}, f)

def save_output_map():
    update_map.update_output_maps()

def main():

    run_preprocessing()
    
    files_with_hash = []
    for vect_map_file in VECT_MAPS.glob("*.json"):
        with open(vect_map_file, 'r', encoding="utf-8") as f:
            vect_map = json.load(f)
        for entry in vect_map.values():
            if isinstance(entry, dict) and "path" in entry and "hash" in entry:
                files_with_hash.append((Path(entry["path"]), entry["hash"]))
            elif isinstance(entry, dict) and "path" in entry:
                files_with_hash.append((Path(entry["path"]), None))
            else:
                files_with_hash.append((Path(entry), None))
    Check_vect_maps_files_are_processed()
    print(f"[📂] Trouvé {len(files_with_hash)} fichiers listés dans les vect_maps")
    total = len(files_with_hash)
    if total == 0:
        print("Aucun fichier à traiter.")
        return
    
    cpu_cores = os.cpu_count() or 2
    max_workers = min(cpu_cores - 1, total)
    print(f"[⚙️] Lancement avec {max_workers} workers sur {total} fichiers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_pipeline, file_path, hash_val)
            for file_path, hash_val in files_with_hash
        ]
        done = 0
        for future in as_completed(futures):
            future.result()
            done += 1
            save_progress(done, total)
            print(f"[⏳] Progression : {done}/{total} fichiers traités") 


if __name__ == "__main__":
    main()
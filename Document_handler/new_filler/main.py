from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os

from .config import INPUT_DIR, VECT_MAPS
from .graph.build_graph import build_graph
from .preprocessing import build_map, update_map

def run_preprocessing():
    build_map.input_maps()
    build_map.output_maps()
    update_map.update_input_maps()

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
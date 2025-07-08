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

def run_pipeline(file_path):
    graph = build_graph()
    state = {"file_path": str(file_path)}
    graph.invoke(state)

def save_progress(done, total, path="progress.json"):
    with open(path, "w") as f:
        json.dump({"done": done, "total": total}, f)

def save_output_map():
    update_map.update_output_maps()

def main():

    run_preprocessing()
    
    files = []
    for vect_map_file in VECT_MAPS.glob("*.json"):
        with open(vect_map_file, 'r', encoding="utf-8") as f:
            vect_map = json.load(f)
        for entry in vect_map.values():
            if isinstance(entry, dict) and "path" in entry:
                files.append(Path(entry["path"]))
            else:
                files.append(Path(entry))
    print(f"[📂] Trouvé {len(files)} fichiers listés dans les vect_maps")
    total = len(files)
    if total == 0:
        print("Aucun fichier à traiter.")
        return
    
    """ # ne pas prendre les fichiers pdf_map.json
    files = list(INPUT_DIR.rglob("*.json")) + list(INPUT_DIR.rglob("*.pdf"))
    files = [f for f in files if "pdf_map.json" not in f.name]
    print(f"[📂] Trouvé {len(files)} fichiers JSON et PDF dans {INPUT_DIR}")
    total = len(files)
    if total == 0:
        print("Aucun fichier à traiter.")
        return
    """
    
    cpu_cores = os.cpu_count() or 2
    max_workers = min(cpu_cores - 1, total)
    print(f"[⚙️] Lancement avec {max_workers} workers sur {total} fichiers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_pipeline, f)
            for f in files
        ]
        done = 0
        for future in as_completed(futures):
            future.result()
            done += 1
            save_progress(done, total)
            print(f"[⏳] Progression : {done}/{total} fichiers traités") 

    save_output_map()

if __name__ == "__main__":
    main()
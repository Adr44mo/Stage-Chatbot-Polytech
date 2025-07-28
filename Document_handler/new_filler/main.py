from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import os
import threading

from .config import INPUT_DIR, VECT_MAPS, VALID_DIR, PROCESSED_DIR, INPUT_MAPS, cp, PROGRESS_DIR
from .graph.build_graph import build_graph
from .preprocessing import build_map, update_map

progress_lock = threading.Lock()

def save_progress(current: int, total: int, status: str):
    """Sauvegarde l'état d'avancement du scraping dans un fichier JSON"""
    progress_path = PROGRESS_DIR / "progress.json"
    with progress_lock:
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump({"current": current, "total": total, "status": status}, f)
            f.flush()
            os.fsync(f.fileno())

def clear_progress(status: str):
    """Supprime le fichier de progression une fois le scraping terminé"""
    progress_path = PROGRESS_DIR / "progress.json"
    with progress_lock:
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump({"current": 0, "total": 1, "status": status}, f)
            f.flush()
            os.fsync(f.fileno())


def force_recover_all_processed_files():
    """Force la récupération de TOUS les fichiers depuis processed vers valid, avec diagnostic détaillé."""
    if not PROCESSED_DIR.exists():
        cp.print_warning("Le dossier processed n'existe pas")
        return 0
    
    if not VALID_DIR.exists():
        VALID_DIR.mkdir(parents=True, exist_ok=True)
        cp.print_info("Dossier valid créé")

    processed_files = list(PROCESSED_DIR.glob("*.json"))
    cp.print_info(f"🔍 Diagnostic: {len(processed_files)} fichiers trouvés dans processed")
    
    if len(processed_files) == 0:
        cp.print_info("Aucun fichier à récupérer dans processed")
        return 0

    moved_count = 0
    error_count = 0
    conflict_count = 0

    for i, processed_file in enumerate(processed_files):
        if not processed_file.is_file():
            continue
            
        dest = VALID_DIR / processed_file.name
        
        # Si le fichier existe déjà dans valid, le remplacer
        if dest.exists():
            try:
                dest.unlink()  # Supprimer l'ancien
                conflict_count += 1
                cp.print_debug(f"Conflit résolu: supprimé {dest.name} existant dans valid")
            except Exception as e:
                cp.print_error(f"Impossible de supprimer le conflit {dest}: {e}")
                error_count += 1
                continue
        
        # Déplacer le fichier
        try:
            processed_file.rename(dest)
            moved_count += 1
            if (i + 1) % 100 == 0:  # Log tous les 100 fichiers
                cp.print_info(f"Progression récupération: {i + 1}/{len(processed_files)}")
        except Exception as e:
            cp.print_error(f"Erreur déplacement {processed_file.name}: {e}")
            error_count += 1

    cp.print_success(f"✅ Récupération terminée: {moved_count} fichiers déplacés, {conflict_count} conflits résolus, {error_count} erreurs")
    return moved_count

def organize_files():
    """Organiser les fichiers en mettant les anciens fichiers validées dans le dossier 'processed'."""
    if not PROCESSED_DIR.exists():
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    if not VALID_DIR.exists():
        VALID_DIR.mkdir(parents=True, exist_ok=True)

    # FORCER la récupération de TOUS les fichiers processed
    cp.print_info("🔄 Force la récupération de TOUS les fichiers depuis processed...")
    recovered = force_recover_all_processed_files()
    
    if recovered > 0:
        cp.print_success(f"✅ {recovered} fichiers récupérés depuis processed vers valid")
    
    # Vérifier combien de fichiers sont maintenant dans valid
    valid_files = list(VALID_DIR.glob('*.json'))
    cp.print_info(f"📊 État actuel: {len(valid_files)} fichiers dans valid_dir")
    
    # NE PAS redéplacer vers processed pour l'instant - juste diagnostiquer
    cp.print_info("ℹ️  Les fichiers restent dans valid_dir pour éviter de les perdre à nouveau")

def already_processed(file_path):
    """Vérifier si le fichier a déjà été traité et s'il a été copié du dossier 'processed' vers le dossier 'validated'."""
    filename = Path(file_path).stem
    
    # Vérifier s'il existe déjà dans valid_dir
    for valid_file in VALID_DIR.glob(f"{filename}.*"):
        if valid_file.is_file():
            cp.print_debug(f"Fichier {filename} déjà présent dans valid_dir")
            return True
    
    # Chercher dans processed_dir et le déplacer vers valid_dir si trouvé
    for processed_file in PROCESSED_DIR.glob(f"{filename}.*"):
        if processed_file.is_file():
            dest = VALID_DIR / processed_file.name
            try:
                processed_file.rename(dest)
                cp.print_debug(f"Récupéré {processed_file.name} depuis processed vers valid")
                return True
            except Exception as e:
                cp.print_error(f"Erreur lors du déplacement de {processed_file} vers {dest}: {e}")
                return False
    
    return False

def Check_vect_maps_files_are_processed():
    """Vérifier si tous les fichiers dans VECT_MAPS ont été traités."""
    for vect_map in INPUT_MAPS.glob("*.json"):
        with open(vect_map, 'r', encoding="utf-8") as f:
            vect_map_data = json.load(f)
        for entry in vect_map_data.values():
            if not already_processed(file_path=entry["path"]):
                cp.print_warning(f"[⚠️] Fichier non traité trouvé : {entry['path']}")
                return False
    cp.print_success("[✅] Tous les fichiers INPUT_MAPS ont été traités.")
    return True

def diagnostic_files():
    """Affiche un diagnostic détaillé de l'état des fichiers dans les différents dossiers."""
    cp.print_info("🔍 === DIAGNOSTIC DES FICHIERS ===")
    
    # Processed dir
    if PROCESSED_DIR.exists():
        processed_files = list(PROCESSED_DIR.glob("*.json"))
        cp.print_info(f"📁 PROCESSED: {len(processed_files)} fichiers")
        if len(processed_files) > 0:
            cp.print_warning(f"⚠️  Il reste {len(processed_files)} fichiers dans processed qui devraient être récupérés")
    else:
        cp.print_info("📁 PROCESSED: dossier n'existe pas")
    
    # Valid dir
    if VALID_DIR.exists():
        valid_files = list(VALID_DIR.glob("*.json"))
        cp.print_info(f"📁 VALID: {len(valid_files)} fichiers")
    else:
        cp.print_info("📁 VALID: dossier n'existe pas")
    
    # Input maps
    total_in_maps = 0
    if INPUT_MAPS.exists():
        for vect_map in INPUT_MAPS.glob("*.json"):
            try:
                with open(vect_map, 'r', encoding="utf-8") as f:
                    vect_map_data = json.load(f)
                total_in_maps += len(vect_map_data)
            except Exception as e:
                cp.print_error(f"Erreur lecture {vect_map}: {e}")
        cp.print_info(f"📋 INPUT_MAPS: {total_in_maps} fichiers référencés")
    
    cp.print_info("🔍 === FIN DIAGNOSTIC ===")

def run_preprocessing():
    # Diagnostic initial
    diagnostic_files()
    
    build_map.input_maps()
    build_map.output_maps()
    update_map.update_input_maps()
    organize_files()
    
    # Diagnostic final
    cp.print_info("📊 État après preprocessing:")
    diagnostic_files()

def run_pipeline(file_path, hash):
    graph = build_graph()
    state = {"file_path": str(file_path), "hash": hash}
    graph.invoke(state)

""" def save_progress(done, total, path="progress.json"):
    with open(path, "w") as f:
        json.dump({"done": done, "total": total}, f) """

def save_output_map():
    update_map.update_output_maps()

def main():

    clear_progress("1/2 - Traitement des fichiers")

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
    cp.print_info(f"[📂] Trouvé {len(files_with_hash)} nouveau(x) fichiers listés dans les vect_maps")
    total = len(files_with_hash)
    if total == 0:
        cp.print_info("Aucun fichier à traiter.")
        return
    
    cpu_cores = os.cpu_count() or 2
    max_workers = min(cpu_cores - 1, total)
    cp.print_info(f"[⚙️] Lancement avec {max_workers} workers sur {total} fichiers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(run_pipeline, file_path, hash_val)
            for file_path, hash_val in files_with_hash
        ]
        done = 0
        for future in as_completed(futures):
            future.result()
            done += 1
            save_progress(done, total, "1/2 - Traitement des fichiers")
            cp.print_info(f"[⏳] Progression : {done}/{total} fichiers traités")

    clear_progress("2/2 - Vectorisation des fichiers")


if __name__ == "__main__":
    main()
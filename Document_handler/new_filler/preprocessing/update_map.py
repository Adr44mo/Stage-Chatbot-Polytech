import json
from pathlib import Path
import tempfile
import os

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    import warnings
    warnings.warn("filelock n'est pas installé. Fonctionnement sans protection contre la concurrence.")

from ..config import INPUT_MAPS, OUTPUT_MAPS, VECT_MAPS


# -------------------------------------------------------------------------------------
# INPUT_MAPS: maps des fichiers présents dans le corpus
# OUTPUT_MAPS: maps des fichiers qu'on a déjà vectorisé
# VECT_MAPS: maps des fichiers qui ont été ajoutés ou modifiés et qu'il faut vectoriser
# -------------------------------------------------------------------------------------


def load_map(path):
    """Charge un fichier JSON avec protection contre les accès concurrents"""
    if not FILELOCK_AVAILABLE:
        # Fallback sans filelock
        if path.exists():
            try:
                with open(path, 'r', encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    lock_path = f"{path}.lock"
    with FileLock(lock_path, timeout=30):
        if path.exists():
            try:
                with open(path, 'r', encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

def save_map(path, data):
    """Sauvegarde un dictionnaire avec écriture atomique et protection concurrence"""
    if not FILELOCK_AVAILABLE:
        # Fallback sans filelock - écriture atomique seulement
        _atomic_write(path, data)
        return
    
    lock_path = f"{path}.lock"
    with FileLock(lock_path, timeout=30):
        _atomic_write(path, data)

def _atomic_write(path, data):
    """Écriture atomique d'un fichier JSON"""
    # S'assurer que le dossier parent existe
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Écriture dans un fichier temporaire puis renommage atomique
    with tempfile.NamedTemporaryFile(
        mode='w', 
        encoding='utf-8', 
        dir=path.parent, 
        prefix=f".{path.name}.", 
        suffix='.tmp',
        delete=False
    ) as temp_file:
        try:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = temp_file.name
        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
    
    # Renommage atomique
    try:
        if os.name == 'nt':  # Windows
            if path.exists():
                path.unlink()
        os.rename(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e
        

def update_input_maps():

    """ Compare input et output pour générer la liste des fichiers à traiter dans vect_maps """

    # On parcourt tous les fichiers de input_maps
    for input_map_file in INPUT_MAPS.glob("*.json"):

        # Charge les maps et initialise la map de vectorisation
        map_name = input_map_file.name
        input_map = load_map(input_map_file)
        output_map_file = OUTPUT_MAPS / map_name
        output_map = load_map(output_map_file)
        vect_map = {}

        # Ajout ou mise à jour d'un nouveau fichier
        for fname, info in input_map.items():
            input_hash = info["hash"]
            input_path = info["path"]
            # Si le fichier est dans input_map mais pas dans output_map -> Ajout
            if fname not in output_map:
                vect_map[fname] = info

            # Si le fichier est dans input_map et output_map mais avec un hash ou un path différent -> Maj
            else : 
                output_hash = output_map[fname]["hash"]
                output_path = output_map[fname]["path"]
                if input_hash != output_hash or input_path != output_path:
                    vect_map[fname] = info

        # Ecrasement du fichier avec uniquement ce qu'on garde 
        vect_map_file = VECT_MAPS / map_name
        save_map(vect_map_file, vect_map)

        #print(f"[OK] Map input mise à jour pour {map_name}")


def update_output_maps():

    """ Compare input et output pour mettre à jour la map d'output """

    output_files = list(OUTPUT_MAPS.glob("*.json"))
    vect_files = list(VECT_MAPS.glob("*.json"))

    # Si output_dir est vide, on copie tous les vect_maps dans output_maps
    if not output_files:
        for vect_map_file in vect_files:
            vect_map = load_map(vect_map_file)
            output_map_file = OUTPUT_MAPS / vect_map_file.name
            save_map(output_map_file, vect_map)
            #print(f"[OK] (init) Map output créée pour {vect_map_file.name} ({len(vect_map)} fichiers)")
        return

    # On parcourt tous les fichiers de input_maps
    for output_map_file in OUTPUT_MAPS.glob("*.json"):

        map_name = output_map_file.name
        output_map = load_map(output_map_file)
        input_map_file = INPUT_MAPS / map_name
        input_map = load_map(input_map_file)
        vect_map_file = VECT_MAPS / map_name
        if not vect_map_file.exists():
            continue
        vect_map = load_map(vect_map_file)

        to_keep = {}

        # Ajout ou mise à jour
        for fname, info in output_map.items():
            if fname in input_map:
                output_hash = info["hash"]
                output_path = info["path"]
                input_hash = output_map[fname]["hash"]
                input_path = output_map[fname]["path"]
                # Si le fichier est non modifié et qu'il est dans input_map et output_map
                if output_hash == input_hash and output_path == input_path:
                    to_keep[fname] = info
                    #print(f"[ADD] {fname}")
        
        # Tous les nouveaux fichiers nouvellement vectorisés vont dans l'output
        for fname, info in vect_map.items():
            to_keep[fname] = info
            #print(f"[ADD/MAJ] {fname}")

        save_map(output_map_file, to_keep)
        #print(f"[OK] Map output mise à jour pour {map_name}")


def update_output_maps_entry(hash, full_path):

    """ Ajoute les fichiers prêts pour la vectorisation à l'output à la fin de la pipeline de traitement """

    # Déduire le nom du fichier d'après le path
    path = Path(full_path)
    name = path.name

    # Déduire le nom de la map à partir du dossier parent
    if "json_scrapes" in path.parts:
        suffix = "json_map.json"
    elif "pdf_scrapes" in path.parts:
        suffix = "pdf_map.json"
    elif "pdf_man" in path.parts:
        suffix = "pdf_man_map.json"
    else:
        raise ValueError("Impossible de déterminer si la map est JSON ou PDF à partir du chemin")

    # Construire le nom du fichier de map
    if suffix == "pdf_man_map.json":
        map_filename = suffix
    else:
        try:
            site_index = path.parts.index("data_sites") + 1
            site_name = path.parts[site_index]
            map_filename = f"{site_name}_{suffix}"
        except (ValueError, IndexError):
            raise ValueError("Chemin invalide : impossible d'extraire le nom du site depuis le dossier 'data_sites'")
    output_map_path = OUTPUT_MAPS / map_filename

    # Charger l’ancienne map, ajouter/modifier l'entrée, et sauvegarder
    output_map = load_map(output_map_path)
    # Vérifie si déjà à jour
    if name in output_map and output_map[name]["hash"] == hash and output_map[name]["path"] == str(path):
        #print(f"[SKIP] '{name}' déjà à jour dans {map_filename}")
        return

    # Sinon, mise à jour
    output_map[name] = {
        "hash": hash,
        "path": str(path)
    }
    save_map(output_map_path, output_map)

    #print(f"[OK] Entrée mise à jour dans {map_filename} pour '{name}'")


def clean_output_maps():

    """ Supprime les fichiers obsolètes (présents dans output mais pas dans input) """

    for output_map_file in OUTPUT_MAPS.glob("*.json"):
        map_name = output_map_file.name
        output_map = load_map(output_map_file)
        input_map = load_map(INPUT_MAPS / map_name)

        cleaned = {
            fname: info
            for fname, info in output_map.items()
            if fname in input_map
        }

        save_map(output_map_file, cleaned)
        #print(f"[CLEAN] {map_name} : {len(output_map) - len(cleaned)} fichiers supprimés")


def clean_map_files():

    """ Supprime les fichiers de map (output et vect) orphelins dont l'input a été supprimé """

    input_map_names = {f.name for f in INPUT_MAPS.glob("*.json")}

    for map_dir in [OUTPUT_MAPS, VECT_MAPS]:
        for map_file in map_dir.glob("*.json"):
            if map_file.name not in input_map_names:
                map_file.unlink()
                #print(f"[DEL] Map supprimée : {map_file.name} (orpheline)")


if __name__ == "__main__":
    update_input_maps()
    #update_output_maps()
    update_output_maps_entry("3be9d83478d21165a4765def6f714bdec74df3672c733d017cfa17eb6692e248", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/pdf_man/charte_bons_comportements.pdf")
    update_output_maps_entry("2724af30251f597eef099fdbd34f4af474dc2c049f8c89634b705806190f6d16", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/pdf_man/MAIN/syllabus/syllabus_MAIN.pdf")
    update_output_maps_entry("77cd2d38a60432c97fde70e939d58536e7ae386963cca82b3daca58a26d22628", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/data_sites/test_site/json_scrapes/artiste.json")
    update_output_maps_entry("f61ec77d04ff9c21ffec6f332f81c40a23cf1a6c55786fcb100cac81b15bfbc1", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/data_sites/test_site/pdf_scrapes/CP_AG_AVOSTTI_VF.pdf")
    clean_output_maps()
    clean_map_files()
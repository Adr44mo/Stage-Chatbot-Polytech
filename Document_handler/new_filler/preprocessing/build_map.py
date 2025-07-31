import json
import hashlib

from ..config import DATA_SITES_DIR, PDF_MAN_DIR, INPUT_MAPS, OUTPUT_MAPS
from .update_map import save_map  # Utilise la fonction sécurisée

EXCLUDED_SITES = {'archives'}


# --------------------------------------------------------------------------------------------
# Construit les maps d'input et initialise les maps d'output si elles n'ont pas déjà été crées
# --------------------------------------------------------------------------------------------


def compute_file_hash(path):
    
    """ Calcule le hash SHA256 d'un fichier PDF pour détecter si ce PDF a été modifié """

    hash_sha256 = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"[ERREUR] Échec du calcul de hash pour {path} : {e}")
        return None
    
def clean_input_maps():

    """ Supprime les aps obsolètes dans INPUT_MAPS (dont le dossier source n'existe plus) """

    expected_map_names = {
        f"{site.name}_pdf_map.json"
        for site in DATA_SITES_DIR.iterdir()
        if site.is_dir() and site.name.lower() not in EXCLUDED_SITES
    }
    expected_map_names |= {
        f"{site.name}_json_map.json"
        for site in DATA_SITES_DIR.iterdir()
        if site.is_dir() and site.name.lower() not in EXCLUDED_SITES and (site / "json_scrapes").exists()
    }
    expected_map_names.add("pdf_man_map.json")

    for map_file in INPUT_MAPS.glob("*.json"):
        if map_file.name not in expected_map_names:
            map_file.unlink()
            #print(f"[CLEAN] Map supprimée : {map_file.name}")


def build_pdf_man_input_map():

    """ Construit la map d'input contenant tous les fichiers qu'on a ajouté manuellement """
    
    pdf_man_map = {}
    for pdf_path in PDF_MAN_DIR.rglob("*.pdf"):

        # Calcule le hash et le chemin
        hash_val = compute_file_hash(pdf_path)
        if hash_val:
            rel_path = pdf_path.name
            pdf_man_map[rel_path] = {
                "hash": hash_val,
                "path": str(pdf_path.resolve())
            }

    # Sauvegarde le fichier dans la map
    input_map = INPUT_MAPS / "pdf_man_map.json"
    save_map(input_map, pdf_man_map)


def build_pdf_man_output_map():

    """ Construit une map vide pour les outputs si la map n'existe pas encore """

    output_map = OUTPUT_MAPS / "pdf_man_map.json"
    if not output_map.exists():
        save_map(output_map, {})


def build_input_maps():

    """ Construit la map d'input contenant les fichiers scrapés à partir des sites """

    # On parcourt tous les dossiers présents dans data_sites sans le dossier d'archives
    for site_dir in DATA_SITES_DIR.iterdir():
        if not site_dir.is_dir() or site_dir.name.lower() in EXCLUDED_SITES:
            continue
        site_name = site_dir.name

        # --- PDF MAP --- : On regarde la map existante concernant les PDF scrapés et on ne garde que les champs qui nous intéressent
        pdf_map_path = site_dir / "pdf_map.json"
        if pdf_map_path.exists():
            try:
                with open(pdf_map_path, "r", encoding="utf-8") as f:
                    pdf_map = json.load(f)

                # On ne garde que le champ "hash" et on construit le path
                hash_only_map = {
                    fname: {
                        "hash": info["hash"],
                        "path": str((site_dir/"pdf_scrapes"/fname).resolve())
                    } 
                    for fname, info in pdf_map.items() if "hash" in info
                }
            
                # Sauvegarde
                input_pdf_map = INPUT_MAPS / f"{site_name}_pdf_map.json"
                save_map(input_pdf_map, hash_only_map)

            except (json.JSONDecodeError, OSError) as e:
                print(f"[ERREUR] Fichier {pdf_map_path} illisible : {e}")

        # --- JSON MAP --- : Crée la map à partir des informations présentes dans chaque document JSON
        json_dir = site_dir / "json_scrapes"
        if json_dir.exists():
            json_map = {}
            for map_file in json_dir.glob("*.json"):
                try:
                    with open(map_file, "r", encoding="utf-8") as f:
                        file_map = json.load(f)
                    # On ne garde que les champs qui nous intéressent : hash et path
                    if "hash" in file_map:
                        json_map[map_file.name] = {
                            "hash": file_map["hash"],
                            "path": str(map_file.resolve())
                        }
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[ERREUR] Fichier JSON {map_file} illisible : {e}")
            # Sauvegarde
            input_json_map = INPUT_MAPS / f"{site_name}_json_map.json"
            save_map(input_json_map, json_map)

        
def build_output_maps():

    """ Initialisation des outputs s'ils n'existent pas pour les fichiers scrapés """

    # On parcourt tous les dossiers présents dans data_sites sans le dossier d'archives
    for site_dir in DATA_SITES_DIR.iterdir():
        if not site_dir.is_dir() or site_dir.name.lower() in EXCLUDED_SITES:
            continue
        site_name = site_dir.name

        # --- PDF MAP ---
        pdf_map_path = site_dir / "pdf_map.json"
        if pdf_map_path.exists():
            output_pdf_map = OUTPUT_MAPS / f"{site_name}_pdf_map.json"
            if not output_pdf_map.exists():
                save_map(output_pdf_map, {})

        # --- JSON MAP ---
        json_dir = site_dir / "json_scrapes"
        if json_dir.exists():
            output_json_map = OUTPUT_MAPS / f"{site_name}_json_map.json"
            if not output_json_map.exists():
                save_map(output_json_map, {})


def input_maps():
    build_pdf_man_input_map()
    build_input_maps()
    clean_input_maps()

def output_maps():
    build_pdf_man_output_map()
    build_output_maps()


if __name__ == "__main__":
    # Dossier INPUT
    input_maps()
    # Dossier OUTPUT
    output_maps()
    

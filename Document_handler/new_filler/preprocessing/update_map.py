import json
from pathlib import Path

INPUT_DIR = Path(__file__).parent / "input_maps"
OUTPUT_DIR = Path(__file__).parent / "output_maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VECT_DIR = Path(__file__).parent / "vect_maps"
VECT_DIR.mkdir(parents=True, exist_ok=True)

def load_map(path):
    if path.exists():
        with open (path, 'r', encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_map(path, data):
    with open (path, 'w', encoding="utf-8") as f:
        return json.dump(data, f, indent=2, ensure_ascii=False)

def update_input_maps():

    # On parcourt tous les fichiers de input_maps
    for input_map_file in INPUT_DIR.glob("*.json"):

        map_name = input_map_file.name
        input_map = load_map(input_map_file)
        output_map_file = OUTPUT_DIR / map_name
        output_map = load_map(output_map_file)

        vect_map = {}

        # Ajout ou mise à jour
        for fname, info in input_map.items():
            input_hash = info["hash"] if isinstance(info, dict) else info
            # Si le fichier est dans input_map mais pas dans output_map -> Ajout
            if fname not in output_map:
                vect_map[fname] = info

            # Si le fichier est dans input_map et output_map mais avec un hash différent -> Maj
            else : 
                output_hash = output_map[fname]["hash"] if isinstance(output_map[fname], dict) else output_map[fname]
                if input_hash != output_hash:
                    vect_map[fname] = info

        # Ecrasement du fichier avec uniquement ce qu'on garde 
        vect_map_file = VECT_DIR / map_name
        save_map(vect_map_file, vect_map)

        #print(f"[OK] Map input mise à jour pour {map_name}")

def update_output_maps():

    output_files = list(OUTPUT_DIR.glob("*.json"))
    vect_files = list(VECT_DIR.glob("*.json"))

    # Si output_dir est vide, on copie tous les vect_maps dans output_maps
    if not output_files:
        for vect_map_file in vect_files:
            vect_map = load_map(vect_map_file)
            output_map_file = OUTPUT_DIR / vect_map_file.name
            save_map(output_map_file, vect_map)
            #print(f"[OK] (init) Map output créée pour {vect_map_file.name} ({len(vect_map)} fichiers)")
        return

    # On parcourt tous les fichiers de input_maps
    for output_map_file in OUTPUT_DIR.glob("*.json"):

        map_name = output_map_file.name
        output_map = load_map(output_map_file)
        input_map_file = INPUT_DIR / map_name
        input_map = load_map(input_map_file)
        vect_map_file = VECT_DIR / map_name
        if not vect_map_file.exists():
            #print(f"[WARN] vect_map {vect_map_file} non trouvé, output_map non modifié.")
            continue
        vect_map = load_map(vect_map_file)

        to_keep = {}

        # Ajout ou mise à jour
        for fname, info in output_map.items():
            if fname in input_map:
                output_hash = info["hash"] if isinstance(info, dict) else info
                input_hash = output_map[fname]["hash"] if isinstance(input_map[fname], dict) else input_map[fname]
                # Si le fichier est non modifié et qu'il est dans input_map et output_map
                if output_hash == input_hash:
                    to_keep[fname] = info
                    #print(f"[ADD] {fname}")
        
        for fname, info in vect_map.items():
            to_keep[fname] = info
            #print(f"[ADD/MAJ] {fname}")

        save_map(output_map_file, to_keep)
        #print(f"[OK] Map output mise à jour pour {map_name}")

def update_output_maps_entry(hash, full_path):

    path = Path(full_path)
    
    # 1. Déduire le nom (clé dans le JSON)
    name = path.name

    # 2. Déduire le nom de la map à partir du dossier parent
    if "json_scrapes" in path.parts:
        suffix = "json_map.json"
    elif "pdf_scrapes" in path.parts:
        suffix = "pdf_map.json"
    elif "pdf_man" in path.parts:
        suffix = "pdf_man_map.json"
    else:
        raise ValueError("Impossible de déterminer si la map est JSON ou PDF à partir du chemin")

    # 3. Construire le nom du fichier de map
    if suffix == "pdf_man_map.json":
        map_filename = suffix
    else:
        # Extraire site_name uniquement si ce n'est pas un pdf_man
        try:
            site_index = path.parts.index("data_sites") + 1
            site_name = path.parts[site_index]
            map_filename = f"{site_name}_{suffix}"
        except (ValueError, IndexError):
            raise ValueError("Chemin invalide : impossible d'extraire le nom du site depuis le dossier 'data_sites'")
    output_map_path = OUTPUT_DIR / map_filename

    # 5. Charger l’ancienne map, ajouter/modifier l'entrée, et sauvegarder
    output_map = load_map(output_map_path)
    output_map[name] = {
        "hash": hash,
        "path": str(path)
    }
    save_map(output_map_path, output_map)

    print(f"[OK] Entrée mise à jour dans {map_filename} pour '{name}'")

if __name__ == "__main__":
    update_input_maps()
    #update_output_maps()
    update_output_maps_entry("3be9d83478d21165a4765def6f714bdec74df3672c733d017cfa17eb6692e248", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/pdf_man/MAIN/charte_bons_comportements.pdf")
    update_output_maps_entry("2724af30251f597eef099fdbd34f4af474dc2c049f8c89634b705806190f6d16", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/pdf_man/MAIN/syllabus_MAIN.pdf")
    update_output_maps_entry("77cd2d38a60432c97fde70e939d58536e7ae386963cca82b3daca58a26d22628", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/data_sites/test_site/json_scrapes/artiste.json")
    update_output_maps_entry("f61ec77d04ff9c21ffec6f332f81c40a23cf1a6c55786fcb100cac81b15bfbc1", "/srv/partage/Stage-Chatbot-Polytech/Document_handler/Corpus/test/data_sites/test_site/pdf_scrapes/CP_AG_AVOSTTI_VF.pdf")
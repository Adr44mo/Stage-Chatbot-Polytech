import json
import hashlib
from pathlib import Path

DATA_SITES_DIR = Path(__file__).parent.parent.parent.parent / "Corpus" / "test" / "data_sites"
PDF_MAN_DIR = Path(__file__).parent.parent.parent.parent / "Corpus" / "test" / "pdf_man"
INPUT_DIR = Path(__file__).parent / "input_maps"
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = Path(__file__).parent / "output_maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_hash(path):
    """Calcule le hash SHA256 d'un fichier PDF"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"[ERREUR] Échec du calcul de hash pour {path} : {e}")
        return None


def build_pdf_man_input_map():
    pdf_man_map = {}
    for pdf_path in PDF_MAN_DIR.rglob("*.pdf"):
        hash_val = compute_file_hash(pdf_path)
        if hash_val:
            rel_path = str(pdf_path.relative_to(PDF_MAN_DIR))
            pdf_man_map[rel_path] = {
                "hash": hash_val,
                "path": str(pdf_path.resolve())
            }
    input_map = INPUT_DIR / "pdf_man_map.json"
    with open(input_map, "w", encoding="utf-8") as f:
        json.dump(pdf_man_map, f, indent=2, ensure_ascii=False)
    #print(f"[OK] Map pdf_manual sauvegardée : {input_map}")


def build_pdf_man_output_map():
    output_map = OUTPUT_DIR / "pdf_man_map.json"
    if not output_map.exists():
        with open(output_map, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
        #print(f"[OK] Map pdf_manual sauvegardée : {output_map}")
    #else :
        #print(f"[SKIP] PDF map déjà existante : {output_map}")


def build_input_maps():

    # On parcourt tous les dossiers présents dans data_sites sans le dossier d'archives
    for site_dir in DATA_SITES_DIR.iterdir():
        if not site_dir.is_dir() or site_dir.name.lower() == "archives":
            continue
        site_name = site_dir.name

        # --- PDF MAP ---
        pdf_map_path = site_dir / "pdf_map.json"
        if pdf_map_path.exists():
            with open(pdf_map_path, "r", encoding="utf-8") as f:
                pdf_map = json.load(f)
            # On ne garde que le champ "hash"
            hash_only_map = {
                fname: {
                    "hash": info["hash"],
                    "path": str((site_dir/"pdf_scrapes"/fname).resolve())
                } 
                for fname, info in pdf_map.items() if "hash" in info
            }
            input_pdf_map = INPUT_DIR / f"{site_name}_pdf_map.json"
            with open(input_pdf_map, "w", encoding="utf-8") as out_f:
                json.dump(hash_only_map, out_f, indent=2, ensure_ascii=False)
            #print(f"[OK] PDF map sauvegardée : {input_pdf_map}")

        # --- JSON MAP ---
        json_dir = site_dir / "json_scrapes"
        if json_dir.exists():
            json_map = {}
            for map_file in json_dir.glob("*.json"):
                with open(map_file, "r", encoding="utf-8") as f:
                    file_map = json.load(f)
                if "hash" in file_map:
                    json_map[map_file.stem] = {
                        "hash": file_map["hash"],
                        "path": str(map_file.resolve())
                    }
            input_json_map = INPUT_DIR / f"{site_name}_json_map.json"
            with open(input_json_map, "w", encoding="utf-8") as out_f:
                json.dump(json_map, out_f, indent=2, ensure_ascii=False)
            #print(f"[OK] JSON map sauvegardée : {input_json_map}")

        
def build_output_maps():

    # On parcourt tous les dossiers présents dans data_sites sans le dossier d'archives
    for site_dir in DATA_SITES_DIR.iterdir():
        if not site_dir.is_dir() or site_dir.name.lower() == "archives":
            continue
        site_name = site_dir.name

        # --- PDF MAP ---
        pdf_map_path = site_dir / "pdf_map.json"
        if pdf_map_path.exists():
            output_pdf_map = OUTPUT_DIR / f"{site_name}_pdf_map.json"
            if not output_pdf_map.exists():
                with open(output_pdf_map, "w", encoding="utf-8") as out_f:
                    json.dump({}, out_f, indent=2, ensure_ascii=False)
                #print(f"[OK] PDF map sauvegardée : {output_pdf_map}")
            #else:
                #print(f"[SKIP] PDF map déjà existante : {output_pdf_map}")

        # --- JSON MAP ---
        json_dir = site_dir / "json_scrapes"
        if json_dir.exists():
            output_json_map = OUTPUT_DIR / f"{site_name}_json_map.json"
            if not output_json_map.exists():
                with open(output_json_map, "w", encoding="utf-8") as out_f:
                    json.dump({}, out_f, indent=2, ensure_ascii=False)
                #print(f"[OK] JSON map sauvegardée : {output_json_map}")

def input_maps():
    build_pdf_man_input_map()
    build_input_maps()

def output_maps():
    build_pdf_man_output_map()
    build_output_maps()


if __name__ == "__main__":
    # Dossier INPUT
    input_maps()
    # Dossier OUTPUT
    output_maps()
    

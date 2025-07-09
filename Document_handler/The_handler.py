import subprocess
from pathlib import Path
from typing import List
from pydantic import BaseModel
import yaml
from typing import List
from typing import Dict
from typing import Optional


from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .scraping.scraping_tool.scraping_script import run_scraping_from_configs
from .scraping.tools.manage_config import generate_config, archive_config
from .scraping.scraping_tool.src.scraper_utils import count_modified_pages

from .new_filler.Vectorisation import vectorisation_chunk
from .new_filler import main as vectorisation_graph_preprocessing

class VectorizationInput(BaseModel):
    vectorstore_dir: Optional[str] = None

router = APIRouter()

SCRAPING_DIR = Path(__file__).resolve().parent / "scraping" / "scraping_tool"
CONFIG_DIR = SCRAPING_DIR / "config_sites"
LOG_DIR = Path(__file__).resolve().parent / "scraping" / "logs"
CORPUS_DIR = Path(__file__).resolve().parent / "Corpus"


def supp_temp_files(temp_dirs):
    for temp_dir in temp_dirs:
        if temp_dir.exists():
            print(f"[🗑️ Suppression des fichiers temporaires dans {temp_dir}]")
            for file in temp_dir.glob("*.json"):
                try:
                    file.unlink()
                    print(f"[✅] Fichier supprimé : {file.name}")
                except Exception as e:
                    print(f"[⚠️ Erreur lors de la suppression de {file.name}]: {e}")
        else:
            print(f"[ℹ️] Le répertoire {temp_dir} n'existe pas, rien à supprimer.")

# TODO: make a route for each step in the pipeline

# Pour l'affichage des informations de chaque site pour le scraping
@router.get("/site_infos")
def get_site_infos():
    try:
        site_infos = []
        for f in CONFIG_DIR.glob("*.yaml"):
            with open(f, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                name = data.get("NAME")
                url = data.get("BASE_URL")
                scraped = data.get("LAST_MODIFIED_DATE")
                new_docs = count_modified_pages(data)
                site_infos.append({"name": name, "url": url, "scraped_at": scraped, "new_docs": new_docs})
        return site_infos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des informations de sites : {e}")

# On récupère le nom des sites à scraper donc on les convertit pour avoir les fichiers de configuration
def site_names_to_config_files(site_names:List[str]) -> List[str]:
    config_files = []
    for f in CONFIG_DIR.glob("*.yaml"):
        with open(f, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            name = data.get("NAME")
            if name in site_names:
                config_files.append(f.name)
    return config_files

# Pour la réalisation du scraping grâce aux fichiers de configuration
@router.post("/scraping")
def run_scraping(config_files: List[str]):
    try:
        run_scraping_from_configs(config_files)
        return {"status": "success", "message": f"Scraping lancé pour : {config_files}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur scraping : {e}")
    
@router.post("/add_site")
def add_site(site_name:str, url:str):
    try:
        generate_config(site_name, url)
        return {"status": "success", "message": f"Site {site_name} ajouté avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du site : {e}")
    
@router.post("/supp_site")
def supp_site(site_name:str):
    try:
        archive_config(site_name)
        return {"status": "success", "message": f"Site {site_name} archivé avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'archivage du site : {e}")

"""
TODO: make a route to delete files that are no longer needed

@router.post("/supp_temp_files")
def delete_temp_files():
    temp_dirs = [
        Path(__file__).parent / "Corpus" / "json_Output_pdf&Scrap",
        Path(__file__).parent / "Corpus" / "json_normalized" / "validated",
        Path(__file__).parent / "Corpus" / "json_normalized" / "processed"
    ]
    supp_temp_files(temp_dirs)
    return {"status": "success", "message": "Temporary files deleted."}
"""

@router.post("/files_normalization")
def run_fill_one():
    vectorisation_graph_preprocessing.main()
    return {"status": "success", "message": "JSON files filled and validated."}


@router.post("/vectorization")
def run_vectorization(data: VectorizationInput):
    if data.vectorstore_dir:
        vectorstore_dir = Path(data.vectorstore_dir)
        vectorisation_chunk.main(VECTORSTORE_DIR=vectorstore_dir)
    else:
        vectorisation_chunk.main()
    return {"status": "success", "message": "Vectorization completed."}


##################### TEMPORARY FILE HANDLER #####################
def run_scripts():
    # SCRAPPING
    subprocess.run(['python', 'Pdf_handler/pdftojson.py'], check=True)
    subprocess.run(['python', 'Pdf_handler/filler/fill_one.py'], check=True)
    subprocess.run(['python', 'Json_handler/normelizejson.py'], check=True)
    subprocess.run(['python', 'Vectorisation/vectorisation_chunk.py'], check=True)
###################################################################

if __name__ == "__main__":
    temp_dirs = [
        Path(__file__).parent.parent / "Corpus" / "json_Output_pdf&Scrap",
        Path(__file__).parent.parent / "Corpus" / "json_normalized" / "validated",
        Path(__file__).parent.parent / "Corpus" / "json_normalized" / "processed"
    ]
    supp_temp_files(temp_dirs)
    run_scripts()
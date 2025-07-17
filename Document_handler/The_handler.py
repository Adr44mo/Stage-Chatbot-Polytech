import yaml
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from .scraping.scraping_tool.scraping_script import run_scraping_from_configs
from .scraping.tools.manage_config import generate_config, archive_config
from .scraping.scraping_tool.src.scraper_utils import count_modified_pages

from .new_filler.Vectorisation import vectorisation_chunk_dev
from .new_filler import main as vectorisation_graph_preprocessing

router = APIRouter()

SCRAPING_DIR = Path(__file__).resolve().parent / "scraping" / "scraping_tool"
CONFIG_DIR = SCRAPING_DIR / "config_sites"
LOG_DIR = Path(__file__).resolve().parent / "scraping" / "logs"
CORPUS_DIR = Path(__file__).resolve().parent / "Corpus"

class VectorizationInput(BaseModel):
    vectorstore_dir: Optional[str] = None

class AddSiteInput(BaseModel):
    siteName:str
    url: str

class SuppSiteInput(BaseModel):
    siteName: str


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
                lastScraped = data.get("LAST_MODIFIED_DATE")
                site_infos.append({"name": name, "url": url, "lastScraped": lastScraped})
        return site_infos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des informations de sites : {e}")
    
# Pour l'affichage du nombre de nouveaux documents pour chaque site
@router.get("/site_new_docs")
def get_site_new_docs():
    try:
        counts = []
        for f in CONFIG_DIR.glob("*.yaml"):
            with open(f, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                name = data.get("NAME")
                url = data.get("BASE_URL")
                newDocs = count_modified_pages(data)  # cette fonction qui prend du temps
                counts.append({"name": name, "url": url, "newDocs": newDocs})
        return counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération compte nouveaux docs : {e}")


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
def run_scraping(siteNames: List[str]):
    try:
        config_files = site_names_to_config_files(siteNames)
        run_scraping_from_configs(config_files)
        return {"status": "success", "message": f"Scraping lancé pour : {config_files}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur scraping : {e}")
    
# Pour la barre de progression lors du scraping
@router.get("/progress/{site_name}")
def get_scraping_progress(site_name: str):

    progress_dir = SCRAPING_DIR / "progress"
    progress_file = progress_dir / f"{site_name}.json"

    if not progress_file.exists():
        raise HTTPException(status_code=404, detail="Pas de progression en cours pour ce site")

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lecture progression : {e}")

    
@router.post("/add_site")
def add_site(data: AddSiteInput):
    try:
        generate_config(data.siteName, data.url)
        return {"status": "success", "message": f"Site {data.siteName} ajouté avec succès."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du site : {e}")
    
@router.post("/supp_site")
def supp_site(data: SuppSiteInput):
    try:
        archive_config(data.siteName)
        return {"status": "success", "message": f"Site {data.siteName} archivé avec succès."}
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

# Pipeline de traitement
@router.post("/files_normalization")
def run_fill_one():
    vectorisation_graph_preprocessing.main()
    return {"status": "success", "message": "JSON files filled and validated."}

# Vectorisation
@router.post("/vectorization")
def run_vectorization():
    result = vectorisation_chunk_dev.build_vectorstore()
    return result

# Pipeline de traitement et vectorisation
@router.post("/process_and_vectorize")
def run_processing_and_vectorizaing():
    try:
        processing_res = vectorisation_graph_preprocessing.main()
        vectorization_res = vectorisation_chunk_dev.build_vectorstore()
        return {
            "status": "success",
            "message": "Traitement et vectorisation terminés.",
            "processing_result": str(processing_res),
            "vectorization_result": str(vectorization_res)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur traitement/vectorisation : {e}")


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
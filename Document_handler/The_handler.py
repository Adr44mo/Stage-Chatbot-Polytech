import subprocess
import os
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
from .Pdf_handler import pdftojson
from .Pdf_handler.filler import fill_one
from .Json_handler import normelizejson
from .Vectorisation import vectorisation_chunk

class PDFJSONInput(BaseModel):
    input_dirs_pdf: Dict[str, str]
    input_dirs_json: Dict[str, str]

class VectorizationInput(BaseModel):
    vectorstore_dir: Optional[str] = None

router = APIRouter()

CONFIG_DIR = Path(__file__).resolve().parent / "scraping" / "scraping_tool" / "config_sites"
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


@router.get("/menu")
def run_menu():
    try:
        config_files = [f.name for f in CONFIG_DIR.glob("*.yaml")]
        site_list = [
            {
                "label": f.replace(".yaml", "").replace("_", " ").title(),
                "value": f
            }
            for f in config_files
        ]
        return site_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des sites : {e}")

@router.post("/scraping")
def run_scraping(config_files: List[str]):
    try:
        run_scraping_from_configs(config_files, str(CONFIG_DIR), str(LOG_DIR))
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

@router.post("/supp_temp_files")
def delete_temp_files():
    temp_dirs = [
        Path(__file__).parent / "Corpus" / "json_Output_pdf&Scrap",
        Path(__file__).parent / "Corpus" / "json_normalized" / "validated",
        Path(__file__).parent / "Corpus" / "json_normalized" / "processed"
    ]
    supp_temp_files(temp_dirs)
    return {"status": "success", "message": "Temporary files deleted."}

@router.post("/pdftojson")
def run_pdftojson(data: PDFJSONInput):
    pdftojson.run_for_input_dirs(data.input_dirs_pdf)
    return {
        "status": "success",
        "message": "PDF to JSON conversion completed."
    }

@router.post("/fill_one")
def run_fill_one():
    fill_one.main()
    return {"status": "success", "message": "JSON files filled and validated."}

@router.post("/normalize_json")
def run_normalize_json(data: PDFJSONInput):
    normelizejson.normalize_all(data.input_dirs_json)
    return {"status": "success", "message": "JSON files normalized."}

@router.post("/vectorization")
def run_vectorization(data: VectorizationInput):
    vectorstore_dir = Path(data.vectorstore_dir) if data.vectorstore_dir else Path(__file__).parent / "vectorstore"
    vectorisation_chunk.main(VECTORSTORE_DIR=vectorstore_dir)
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
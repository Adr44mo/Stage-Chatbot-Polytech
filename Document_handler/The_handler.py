import subprocess
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .Pdf_handler import pdftojson
from .Pdf_handler.filler import fill_one


router = APIRouter()


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

@router.get("supp_temp_files")
def delete_temp_files():
    temp_dirs = [
        Path(__file__).parent.parent / "Corpus" / "json_Output_pdf&Scrap",
        Path(__file__).parent.parent / "Corpus" / "json_normalized" / "validated",
        Path(__file__).parent.parent / "Corpus" / "json_normalized" / "processed"
    ]
    supp_temp_files(temp_dirs)
    return {"status": "success", "message": "Temporary files deleted."}

@router.get("pdftojson")
def run_pdftojson(intput_dirs: list[str] = pdftojson.INPUT_DIRS):
    pdftojson.run_for_input_dirs(intput_dirs)
    return {"status": "success", "message": "PDF to JSON conversion completed."}


@router.get("fill_one")
def run_fill_one():
    fill_one.main()
    return {"status": "success", "message": "JSON files filled and validated."}



##################### TEMPORARY FILE HANDLER #####################
def run_scripts():
    # SCRAPPING
    subprocess.run(['python', 'Pdf_handler/pdftojson.py'], check=True)
    subprocess.run(['python', 'Pdf_handler/filler/fill_one.py'], check=True)
    subprocess.run(['python', 'Json_handler/normelizejson.py'], check=True)
    subprocess.run(['python', 'Vectorisation/vectorisation&chunk.py'], check=True)
###################################################################

if __name__ == "__main__":
    temp_dirs = [
        Path(__file__).parent.parent / "Corpus" / "json_Output_pdf&Scrap",
        Path(__file__).parent.parent / "Corpus" / "json_normalized" / "validated",
        Path(__file__).parent.parent / "Corpus" / "json_normalized" / "processed"
    ]
    supp_temp_files(temp_dirs)
    run_scripts()
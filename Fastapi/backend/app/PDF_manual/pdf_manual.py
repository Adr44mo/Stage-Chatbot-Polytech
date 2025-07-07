from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import shutil
import os
from datetime import datetime
from typing import List

# Configuration du corpus PDF
CORPUS_RELATIVE_PATH = "Document_handler/Corpus/pdf_man"
PDF_MANUAL_DIR = Path(__file__).parent.parent.parent.parent.parent / CORPUS_RELATIVE_PATH

router = APIRouter()


@router.post("/admin/upload-files")
def upload_files(
    files: List[UploadFile] = File(...),
    dir: str = Form(...),  # nom de projet ou utilisateur pour organiser dans un sous-répertoire
):
    base_dir = PDF_MANUAL_DIR
    target_dir = base_dir / dir
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            continue  # ignore les non-pdf

        file_path = target_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(str(file_path))

    return {"message": "Files uploaded successfully", "saved": saved_files}

@router.get("/admin/config")
def get_corpus_config():
    """
    Retourne la configuration du corpus PDF.
    """
    return {
        "corpus_root_path": CORPUS_RELATIVE_PATH
    }

@router.get("/admin/list-dirs")
def list_dirs():
    return {"directories": [d.name for d in PDF_MANUAL_DIR.iterdir() if d.is_dir()]}

@router.get("/admin/list-files/{dir}")
def list_files(dir: str):
    target_dir = PDF_MANUAL_DIR / dir
    if not target_dir.exists() or not target_dir.is_dir():
        return {"error": "Directory does not exist"}

    files = []
    for file_path in target_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".pdf":
            stat = file_path.stat()
            created_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d")
            modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
            
            files.append({
                "name": file_path.name,
                "date_added": created_time,
                "date_modified": modified_time,
                "size": stat.st_size
            })
    
    return {"files": files}

@router.get("/admin/list-all-files")
def list_all_files():
    all_files = []
    for dir in PDF_MANUAL_DIR.iterdir():
        if dir.is_dir():
            for file_path in dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == ".pdf":
                    # Récupérer les métadonnées du fichier
                    stat = file_path.stat()
                    created_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d")
                    modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                    
                    all_files.append({
                        "dir": dir.name, 
                        "file": file_path.name,
                        "date_added": created_time,
                        "date_modified": modified_time,
                        "size": stat.st_size
                    })
    return {"files": all_files}

@router.delete("/admin/delete-file/{dir}/{filename}")
def delete_file(dir: str, filename: str):
    file_path = PDF_MANUAL_DIR / dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be deleted")

    file_path.unlink()
    return {"message": f"{filename} deleted successfully"}

@router.delete("/admin/delete-dir/{dir}")
def delete_dir(dir: str, force: bool = False):
    dir_path = PDF_MANUAL_DIR / dir
    if not dir_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if any(dir_path.iterdir()) and not force:
        raise HTTPException(status_code=400, detail="Directory is not empty. Use `force=true` to delete.")

    shutil.rmtree(dir_path)
    return {"message": f"Directory '{dir}' deleted successfully"}

@router.get("/admin/download-file/{dir}/{filename}")
def download_file(dir: str, filename: str):
    file_path = PDF_MANUAL_DIR / dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be downloaded")

    return {"file_path": str(file_path)}

@router.get("/admin/download-dir/{dir}")
def download_dir(dir: str):
    dir_path = PDF_MANUAL_DIR / dir
    if not dir_path.exists() or not dir_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    # Zip the directory for download
    zip_path = dir_path.with_suffix(".zip")
    shutil.make_archive(zip_path.with_suffix(""), 'zip', dir_path)

    return {"zip_file": str(zip_path)}

# renommer un fichier PDF
@router.post("/admin/rename-file/{dir}/{old_filename}")
def rename_file(dir: str, old_filename: str, new_filename: str):
    old_file_path = PDF_MANUAL_DIR / dir / old_filename
    if not old_file_path.exists() or not old_file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not old_file_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be renamed")

    new_file_path = PDF_MANUAL_DIR / dir / new_filename
    if new_file_path.exists():
        raise HTTPException(status_code=400, detail="File with new name already exists")

    old_file_path.rename(new_file_path)
    return {"message": "File renamed successfully"}

@router.post("/admin/move-file")
def move_file(
    dir: str = Form(...),  # nom de projet ou utilisateur source
    filename: str = Form(...),  # nom du fichier à déplacer
    target_dir: str = Form(...)  # nom du projet ou utilisateur cible
):
    source_path = PDF_MANUAL_DIR / dir / filename
    if not source_path.exists() or not source_path.is_file():
        raise HTTPException(status_code=404, detail="Source file not found")
    if not source_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be moved")

    target_path = PDF_MANUAL_DIR / target_dir / filename
    target_path.parent.mkdir(parents=True, exist_ok=True)

    source_path.rename(target_path)
    return {"message": "File moved successfully", "new_location": str(target_path)}


@router.post("/admin/crate-dir")
def create_dir(dir: str):
    """
    Crée un nouveau répertoire pour stocker les fichiers PDF.
    """
    new_dir = PDF_MANUAL_DIR / dir
    if new_dir.exists():
        raise HTTPException(status_code=400, detail="Directory already exists")
    
    new_dir.mkdir(parents=True, exist_ok=True)
    return {"message": f"Directory '{dir}' created successfully", "path": str(new_dir)}
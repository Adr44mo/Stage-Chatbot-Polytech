# ======================================================
# Routes pour la gestion des fichiers PDF dans le corpus
# ======================================================

# Imports des bibliothèques nécessaires
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import shutil
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Configuration du corpus PDF
CORPUS_RELATIVE_PATH = "Document_handler/Corpus/pdf_man"
PDF_MANUAL_DIR = Path(__file__).parent.parent.parent.parent.parent / CORPUS_RELATIVE_PATH

router = APIRouter()

# ================
# Modèles Pydantic
# ================

class FileOperation(BaseModel):
    """Modèle pour les opérations sur les fichiers"""
    operation: str
    path: str
    new_path: Optional[str] = None
    new_name: Optional[str] = None

class DirectoryItem(BaseModel):
    """Modèle pour représenter un élément de l'arborescence (fichier ou dossier)"""
    name: str
    path: str
    type: str  # "file" ou "directory"
    size: Optional[int] = None
    date_added: Optional[str] = None
    date_modified: Optional[str] = None
    children: Optional[List["DirectoryItem"]] = None

DirectoryItem.model_rebuild()  # Nécessaire pour la référence circulaire

# =====================
# Fonctions utilitaires
# =====================

def is_safe_path(path: str) -> bool:
    """Vérifie que le chemin est bien dans le corpus"""
    try:
        full_path = PDF_MANUAL_DIR / path
        full_path.resolve().relative_to(PDF_MANUAL_DIR.resolve())
        return True
    except ValueError:
        return False

def is_corpus_root(path: str) -> bool:
    """Vérifie si le chemin correspond au dossier 'corpus' racine"""
    return path == "" or path == "." or path == PDF_MANUAL_DIR.name


# =======================================
# Routes pour la gestion des fichiers PDF
# =======================================

@router.get("/admin/config")
def get_corpus_config():
    """
    Retourne la configuration du corpus PDF (chemin de base).
    """
    return {
        "corpus_root_path": CORPUS_RELATIVE_PATH
    }


@router.get("/admin/tree")
def get_corpus_tree(path: str = ""):
    """
    Retourne l'arborescence complète du corpus.
    """
    if not is_safe_path(path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    current_path = PDF_MANUAL_DIR / path if path else PDF_MANUAL_DIR
    
    def build_tree(directory: Path, relative_path: str = "") -> List[DirectoryItem]:
        """Construit récursivement l'arborescence des fichiers et dossiers."""
        items = []
        for item in sorted(directory.iterdir()):
            item_relative_path = f"{relative_path}/{item.name}" if relative_path else item.name
            
            if item.is_dir():
                # Dossier
                stat = item.stat()
                created_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                
                dir_item = DirectoryItem(
                    name=item.name,
                    path=item_relative_path,
                    type="directory",
                    date_added=created_time,
                    date_modified=modified_time,
                    children=build_tree(item, item_relative_path)
                )
                items.append(dir_item)
            
            elif item.is_file() and item.suffix.lower() == ".pdf":
                # Fichier PDF
                stat = item.stat()
                created_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                
                file_item = DirectoryItem(
                    name=item.name,
                    path=item_relative_path,
                    type="file",
                    size=stat.st_size,
                    date_added=created_time,
                    date_modified=modified_time
                )
                items.append(file_item)
        
        return items
    
    return {"tree": build_tree(current_path, path)}


# @router.get("/admin/list-dirs")
# def list_dirs():
#     """
#     Retourne la liste des répertoires dans le corpus PDF.
#     """
#     return {"directories": [d.name for d in PDF_MANUAL_DIR.iterdir() if d.is_dir()]}


# @router.get("/admin/list-files/{dir}")
# def list_files(dir: str):
#     """
#     Retourne la liste des fichiers PDF dans un répertoire spécifique.
#     """
#     if not is_safe_path(dir):
#         raise HTTPException(status_code=400, detail="Invalid path")
    
#     target_dir = PDF_MANUAL_DIR / dir
#     if not target_dir.exists() or not target_dir.is_dir():
#         return {"error": "Directory does not exist"}

#     files = []
#     for file_path in target_dir.iterdir():
#         if file_path.is_file() and file_path.suffix.lower() == ".pdf":
#             stat = file_path.stat()
#             created_time = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d")
#             modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
            
#             files.append({
#                 "name": file_path.name,
#                 "date_added": created_time,
#                 "date_modified": modified_time,
#                 "size": stat.st_size
#             })
    
#     return {"files": files}


@router.get("/admin/list-all-files")
def list_all_files():
    """
    Liste tous les fichiers PDF du corpus de manière récursive
    """
    all_files = []
    
    def scan_directory(directory: Path, relative_path: str = ""):
        for item in directory.iterdir():
            if item.is_dir():
                sub_path = f"{relative_path}/{item.name}" if relative_path else item.name
                scan_directory(item, sub_path)
            elif item.is_file() and item.suffix.lower() == ".pdf":
                stat = item.stat()
                created_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                
                all_files.append({
                    "dir": relative_path if relative_path else "root",
                    "file": item.name,
                    "date_added": created_time,
                    "date_modified": modified_time,
                    "size": stat.st_size
                })
    
    scan_directory(PDF_MANUAL_DIR)
    return {"files": all_files}


@router.get("/admin/dir-info")
def get_dir_info(dir_path: str = ""):
    """Retourne des informations sur un dossier (nombre de fichiers, taille, etc.)"""
    if not is_safe_path(dir_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    full_path = PDF_MANUAL_DIR / dir_path if dir_path else PDF_MANUAL_DIR
    if not full_path.exists() or not full_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    file_count = 0
    dir_count = 0
    total_size = 0
    
    def count_recursive(path: Path):
        nonlocal file_count, dir_count, total_size
        for item in path.iterdir():
            if item.is_dir():
                dir_count += 1
                count_recursive(item)
            elif item.is_file() and item.suffix.lower() == ".pdf":
                file_count += 1
                total_size += item.stat().st_size
    
    count_recursive(full_path)
    
    return {
        "path": dir_path if dir_path else "root",
        "file_count": file_count,
        "dir_count": dir_count,
        "total_size": total_size,
        "can_be_deleted": not is_corpus_root(dir_path),
        "can_be_renamed": not is_corpus_root(dir_path),
        "can_be_moved": not is_corpus_root(dir_path)
    }


@router.delete("/admin/delete-file")
def delete_file(file_path: str):
    """
    Supprime un fichier PDF du corpus.
    """
    if not is_safe_path(file_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    full_path = PDF_MANUAL_DIR / file_path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not full_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be deleted")

    full_path.unlink()
    return {"message": f"File deleted successfully"}


@router.delete("/admin/delete-dir")
def delete_dir(dir_path: str, force: bool = False):
    """
    Supprime un dossier du corpus.
    """
    if not is_safe_path(dir_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if is_corpus_root(dir_path):
        raise HTTPException(status_code=403, detail="Cannot delete corpus root directory")
    
    full_path = PDF_MANUAL_DIR / dir_path
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if any(full_path.iterdir()) and not force:
        raise HTTPException(status_code=400, detail="Directory is not empty. Use `force=true` to delete.")

    shutil.rmtree(full_path)
    return {"message": f"Directory deleted successfully"}


@router.post("/admin/upload-files")
def upload_files(files: List[UploadFile] = File(...), dir: str = Form(...)):
    """
    Upload des fichiers PDF dans un répertoire spécifique du corpus.
    """
    if not is_safe_path(dir):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    base_dir = PDF_MANUAL_DIR
    target_dir = base_dir / dir
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename.endswith(".pdf"):
            continue

        file_path = target_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(str(file_path))

    return {"message": "Files uploaded successfully", "saved": saved_files}


@router.post("/admin/create-dir")
def create_dir(dir_path: str = Form(...)):
    """
    Crée un nouveau répertoire dans le corpus.
    """
    if not is_safe_path(dir_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    new_dir = PDF_MANUAL_DIR / dir_path
    if new_dir.exists():
        raise HTTPException(status_code=400, detail="Directory already exists")
    
    new_dir.mkdir(parents=True, exist_ok=True)
    
    # Tracker la création dans tous les snapshots actifs
    for snapshot in corpus_snapshots.values():
        if hasattr(snapshot, 'track_creation'):
            snapshot.track_creation(dir_path)
    
    return {"message": f"Directory created successfully", "path": str(new_dir)}


@router.post("/admin/rename-file")
def rename_file(file_path: str = Form(...), new_name: str = Form(...)):
    """
    Renomme un fichier PDF du corpus.
    """
    if not is_safe_path(file_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    old_path = PDF_MANUAL_DIR / file_path
    if not old_path.exists() or not old_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if not old_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be renamed")

    # Assurer que le nouveau nom a l'extension .pdf
    if not new_name.endswith(".pdf"):
        new_name += ".pdf"

    new_path = old_path.parent / new_name
    if new_path.exists():
        raise HTTPException(status_code=400, detail="File with new name already exists")

    old_path.rename(new_path)
    return {"message": "File renamed successfully"}


@router.post("/admin/rename-dir")
def rename_dir(dir_path: str = Form(...), new_name: str = Form(...)):
    """
    Renomme un dossier du corpus.
    """
    if not is_safe_path(dir_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if is_corpus_root(dir_path):
        raise HTTPException(status_code=403, detail="Cannot rename corpus root directory")
    
    old_path = PDF_MANUAL_DIR / dir_path
    if not old_path.exists() or not old_path.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    new_path = old_path.parent / new_name
    if new_path.exists():
        raise HTTPException(status_code=400, detail="Directory with new name already exists")

    old_path.rename(new_path)
    return {"message": "Directory renamed successfully"}


@router.post("/admin/move-file")
def move_file(
    source_path: str = Form(...),  # chemin source du fichier
    target_path: str = Form(...)   # chemin cible (dossier de destination)
):
    """Déplace un fichier PDF d'un dossier à un autre"""
    if not is_safe_path(source_path) or not is_safe_path(target_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    source_full_path = PDF_MANUAL_DIR / source_path
    if not source_full_path.exists() or not source_full_path.is_file():
        raise HTTPException(status_code=404, detail="Source file not found")
    if not source_full_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files can be moved")

    target_dir = PDF_MANUAL_DIR / target_path
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_full_path = target_dir / source_full_path.name
    if target_full_path.exists():
        raise HTTPException(status_code=400, detail="File already exists in target directory")

    # source_full_path.rename(target_full_path)
    shutil.copy2(source_full_path, target_full_path)
    source_full_path.unlink()
    return {"message": "File moved successfully", "new_location": str(target_full_path)}


@router.post("/admin/move-dir")
def move_dir(
    source_path: str = Form(...),  # chemin source du dossier
    target_path: str = Form(...)   # chemin cible (dossier parent de destination)
):
    """Déplace un dossier d'un endroit à un autre"""
    if not is_safe_path(source_path) or not is_safe_path(target_path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if is_corpus_root(source_path):
        raise HTTPException(status_code=403, detail="Cannot move corpus root directory")
    
    source_full_path = PDF_MANUAL_DIR / source_path
    if not source_full_path.exists() or not source_full_path.is_dir():
        raise HTTPException(status_code=404, detail="Source directory not found")

    target_dir = PDF_MANUAL_DIR / target_path
    target_dir.mkdir(parents=True, exist_ok=True)
    
    target_full_path = target_dir / source_full_path.name
    if target_full_path.exists():
        raise HTTPException(status_code=400, detail="Directory already exists in target location")

    # source_full_path.rename(target_full_path)
    shutil.copytree(source_full_path, target_full_path, copy_function=shutil.copy2)
    shutil.rmtree(source_full_path)
    return {"message": "Directory moved successfully", "new_location": str(target_full_path)}


# =============================================================
# Gestion des modes lecture/écriture et snapshots (sauvegardes)
# =============================================================

corpus_snapshots = {}  # Store pour les snapshots temporaires

class CorpusSnapshot:
    """Classe pour gérer un snapshot du corpus PDF."""
    def __init__(self, snapshot_id: str):
        self.snapshot_id = snapshot_id
        self.backup_path = None  # Chemin de la sauvegarde complète
        self.created_items = []  # Chemins des éléments créés
    
    def create_backup(self):
        """Crée une sauvegarde complète du corpus"""
        import tempfile
        
        try:
            # Créer un dossier temporaire pour la sauvegarde
            backup_dir = Path(tempfile.mkdtemp(prefix="corpus_backup_"))
            
            # Copier tout le corpus
            if PDF_MANUAL_DIR.exists():
                shutil.copytree(PDF_MANUAL_DIR, backup_dir / "corpus_backup", dirs_exist_ok=True)
                self.backup_path = backup_dir / "corpus_backup"
                print(f"Backup créé dans: {self.backup_path}")
            return True
        except Exception as e:
            print(f"Erreur lors de la création du backup: {e}")
            return False
    
    def restore_from_backup(self):
        """Restaure le corpus depuis la sauvegarde"""
        if not self.backup_path or not self.backup_path.exists():
            return False
        
        try:
            # Supprimer le corpus actuel
            if PDF_MANUAL_DIR.exists():
                shutil.rmtree(PDF_MANUAL_DIR)
            
            # Restaurer depuis la sauvegarde
            shutil.copytree(self.backup_path, PDF_MANUAL_DIR)
            print(f"Corpus restauré depuis: {self.backup_path}")
            return True
        except Exception as e:
            print(f"Erreur lors de la restauration: {e}")
            return False
    
    def cleanup_backup(self):
        """Supprime la sauvegarde"""
        if self.backup_path and self.backup_path.parent.exists():
            try:
                shutil.rmtree(self.backup_path.parent)
                print(f"Backup supprimé: {self.backup_path.parent}")
            except Exception as e:
                print(f"Erreur lors de la suppression du backup: {e}")
    
    def track_creation(self, path: str):
        self.created_items.append(path)


# =====================================================
# Routes pour la gestion des modes édition et snapshots
# =====================================================

@router.get("/admin/edit-status")
def get_edit_status():
    """Retourne l'état actuel du mode édition"""
    snapshot_id = None
    if corpus_snapshots:
        # Prendre le premier snapshot_id disponible (il ne devrait y en avoir qu'un)
        snapshot_id = list(corpus_snapshots.keys())[0]
    
    return {
        "edit_mode": len(corpus_snapshots) > 0,
        "active_snapshots": len(corpus_snapshots),
        "snapshot_id": snapshot_id
    }

@router.post("/admin/enable-edit-mode")
def enable_edit_mode():
    """Active le mode édition et crée une sauvegarde"""
    import time
    
    snapshot_id = str(int(time.time()))
    snapshot = CorpusSnapshot(snapshot_id)
    
    # Créer une sauvegarde complète
    if not snapshot.create_backup():
        raise HTTPException(status_code=500, detail="Failed to create backup")
    
    corpus_snapshots[snapshot_id] = snapshot
    
    return {
        "message": "Edit mode enabled with full backup",
        "snapshot_id": snapshot_id,
        "edit_mode": True
    }

@router.post("/admin/save-changes")
def save_changes(snapshot_id: str = Form(...)):
    """Sauvegarde les changements et désactive le mode édition"""
    if snapshot_id not in corpus_snapshots:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    snapshot = corpus_snapshots[snapshot_id]
    
    # Supprimer la sauvegarde puisqu'on confirme les changements
    snapshot.cleanup_backup()
    
    # Supprimer le snapshot
    del corpus_snapshots[snapshot_id]
        
    return {
        "message": "Changes saved successfully",
        "edit_mode": False
    }

@router.post("/admin/cancel-changes")
def cancel_changes(snapshot_id: str = Form(...)):
    """Annule tous les changements en restaurant depuis la sauvegarde"""
    if snapshot_id not in corpus_snapshots:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    snapshot = corpus_snapshots[snapshot_id]
    
    try:
        # Restaurer depuis la sauvegarde
        if not snapshot.restore_from_backup():
            raise HTTPException(status_code=500, detail="Failed to restore from backup")
        
        # Nettoyer la sauvegarde
        snapshot.cleanup_backup()
        
        # Supprimer le snapshot
        del corpus_snapshots[snapshot_id]
        
        return {
            "message": "All changes cancelled - corpus restored from backup",
            "edit_mode": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel changes: {str(e)}")

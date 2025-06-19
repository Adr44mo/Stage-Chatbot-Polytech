# serve_files.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# Root directory for all served files
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent   # Adjust if needed

# Only allow these file types
ALLOWED_EXTENSIONS = {".pdf", ".json"}

@router.get("/files/{file_path:path}")
def serve_file(file_path: str):
    file_location = BASE_DIR / file_path

    try:
        # Fully resolve and ensure it exists
        file_location = file_location.resolve(strict=True)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    # Security check: path must stay inside BASE_DIR
    if not str(file_location).startswith(str(BASE_DIR)):
        raise HTTPException(status_code=403, detail="Access forbidden")

    # Check for allowed file extensions
    if file_location.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type")

    media_type = "application/pdf" if file_location.suffix == ".pdf" else "application/json"
    return FileResponse(path=file_location, media_type=media_type)

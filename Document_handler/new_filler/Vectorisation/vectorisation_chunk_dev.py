import os
import json
import uuid
import logging
import threading
from pathlib import Path
from datetime import datetime

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from ..logic.chunck_syll import chunk_syllabus_for_rag
from ..logic.chunk_docs import adaptive_semantic_chunk
from ..config import OPENAI_API_KEY, VALID_DIR, PROGRESS_DIR

from color_utils import cp
from Fastapi.backend.app.llmm import clean_and_reload_vectorstore

progress_lock = threading.Lock()

def save_progress(current: int, total: int, status: str):
    """Sauvegarde l'état d'avancement du scraping dans un fichier JSON"""
    progress_path = PROGRESS_DIR / "progress.json"
    with progress_lock:
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump({"current": current, "total": total, "status": status}, f)
            f.flush()
            os.fsync(f.fileno())

def clear_progress(status: str):
    """Supprime le fichier de progression une fois le scraping terminé"""
    progress_path = PROGRESS_DIR / "progress.json"
    with progress_lock:
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump({"current": 0, "total": 1, "status": status}, f)
            f.flush()
            os.fsync(f.fileno())

# ---------------------------------------------------------------------------
# Config & logging -----------------------------------------------------------
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

NORMALIZED_DIR: Path = VALID_DIR  # dossier contenant les JSON normalisés
VECTORSTORE_DIR: Path = Path(__file__).parent / "vectorstore_Syllabus"  # dossier final
_BUILD_DIR: Path = VECTORSTORE_DIR.parent / "vectorstore_Syllabus_Construct"  # dossier de build temp
_BACKUP_DIR: Path = VECTORSTORE_DIR.parent / "vectorstore_backup"  # backups successifs

# Taille des chunks / batchs -------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
BATCH_SIZE = 100  # nombre de Documents par lot lors de l'insertion Chroma

# ---------------------------------------------------------------------------
# Outils utilitaires ---------------------------------------------------------
# ---------------------------------------------------------------------------

def _split_list(data: list, size: int):
    """Yield successive *size*-sized chunks from *data*."""
    for i in range(0, len(data), size):
        yield data[i : i + size]


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _check_write_permissions(directory: Path):
    if not os.access(directory, os.W_OK):
        raise PermissionError(f"Le répertoire {directory} n'est pas accessible en écriture.")
    sqlite_file = directory / "chroma.sqlite3"
    if sqlite_file.exists() and not os.access(sqlite_file, os.W_OK):
        raise PermissionError(f"Le fichier {sqlite_file} n'est pas accessible en écriture.")


def _backup_existing_vectorstore():
    if not VECTORSTORE_DIR.exists():
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _ensure_dir(_BACKUP_DIR)
    backup_path = _BACKUP_DIR / f"vectorstore_backup_{timestamp}"
    VECTORSTORE_DIR.rename(backup_path)
    logging.info("🗂️  Ancien vectorstore sauvegardé ⟶ %s", backup_path)


# ---------------------------------------------------------------------------
# Chargement / conversion des documents -------------------------------------
# ---------------------------------------------------------------------------

def _load_json_docs():
    docs = []
    for json_file in NORMALIZED_DIR.glob("*.json"):
        if "syllabus" in json_file.name:
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                docs.append(json.load(f))
        except json.JSONDecodeError as exc:
            logging.warning("⚠️  JSONDecodeError %s: %s", json_file.name, exc)
    return docs


def _load_syllabus_json_docs():
    syllabus_docs = []
    for json_file in NORMALIZED_DIR.glob("**/syllabus*.json*"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                syllabus_docs.append(json.load(f))
        except json.JSONDecodeError as exc:
            logging.warning("⚠️  JSONDecodeError %s: %s", json_file.name, exc)
    return syllabus_docs


def _flatten_metadata(md: dict) -> dict:
    flat = {}
    for key, value in md.items():
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                flat[f"{key}.{sub_key}"] = str(sub_val)
        elif isinstance(value, list):
            flat[key] = ", ".join(map(str, value))
        else:
            flat[key] = str(value)
    return flat


def _ensure_polytech_structure(doc: dict) -> dict:
    """Retourne un doc conforme au schéma attendu."""
    if (
        doc.get("document_type")
        and doc.get("metadata")
        and doc.get("source")
        and "chemin_local" in doc.get("source", {})
    ):
        return doc
    return {
        "document_type": doc.get("document_type", "page_web"),
        "metadata": {
            "title": doc.get("metadata", {}).get("title", doc.get("title", "")),
        },
        "source": {
            "category": doc.get("source", {}).get("category", "scrapping"),
            "chemin_local": doc.get("source", {}).get("chemin_local", ""),
            **({"url": doc["source"]["url"]} if doc.get("source", {}).get("url") else {}),
            **({"site": doc["source"]["site"]} if doc.get("source", {}).get("site") else {}),
        },
        "content": doc.get("content", ""),
        "tags": doc.get("tags", []),
    }


def _chunk_raw_docs(raw_docs: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    lc_docs: list[Document] = []
    for doc in raw_docs:
        content = doc.get("content", "").strip()
        if not content:
            continue
        normalized = _ensure_polytech_structure(doc)
        flat_md = _flatten_metadata({k: v for k, v in normalized.items() if k != "content"})
        # for chunk in splitter.split_text(content):
        for chunk in adaptive_semantic_chunk(content, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
            lc_docs.append(Document(page_content=chunk, metadata=flat_md))
    return lc_docs


def _syllabus_to_lc_docs(syllabus_raw: list[dict]) -> list[Document]:
    lc_docs: list[Document] = []
    for syl in chunk_syllabus_for_rag(syllabus_raw):
        content = syl.get("content", "").strip()
        if not content:
            continue
        normalized = _ensure_polytech_structure(syl)
        flat_md = _flatten_metadata({k: v for k, v in normalized.items() if k != "content"})
        lc_docs.append(Document(page_content=content, metadata=flat_md))
    return lc_docs


# ---------------------------------------------------------------------------
# Pipeline principal ---------------------------------------------------------
# ---------------------------------------------------------------------------

def build_vectorstore() -> dict:
    """Construit le vectorstore Chroma à partir des JSON + syllabus."""

    save_progress(0, 1, "2/2 - Initialisation vectorisation")

    try:
        _ensure_dir(_BUILD_DIR)
        _check_write_permissions(_BUILD_DIR)

        # 1) Chargement & conversion -------------------------------------------------
        logging.info("📄 Chargement des documents JSON normalisés…")
        save_progress(0, 4, "2/2 - Chargement des documents")

        raw_docs = _load_json_docs()
        syllabus_raw = _load_syllabus_json_docs()

        save_progress(1, 4, "2/2 - Conversion en chunks")
        lc_docs = _chunk_raw_docs(raw_docs) + _syllabus_to_lc_docs(syllabus_raw)
        logging.info("✅ %s chunks prêts à être vectorisés.", len(lc_docs))

        if not lc_docs:
            return {"status": "error", "message": "Aucun document à vectoriser."}

        # 2) EmbeddingFunction unique (une seule instance) ---------------------------
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

        # 3) Insertion batchée --------------------------------------------------------
        batches = list(_split_list(lc_docs, BATCH_SIZE))
        first_batch, *rest = batches

        save_progress(2, 4, "2/2 - Création base vectorielle")
        logging.info("💾 Création de la base Chroma (%s docs)…", len(first_batch))
        db = Chroma.from_documents(
            documents=first_batch,
            embedding=embeddings,
            persist_directory=str(_BUILD_DIR),
        )

        total_batches = len(batches)
        for i, batch in enumerate(rest, start=2):
            logging.info("➕ Ajout batch %s/%s (%s docs)…", i, total_batches, len(batch))
            # ids uniques impératifs si on fournit ids → ici on laisse Chroma gérer UUID
            db.add_documents(batch)

            progress_ratio = (i - 1) / (total_batches - 1) if total_batches > 1 else 1
            current_progress = 3 + progress_ratio
            save_progress(int(current_progress * 100), 400, f"2/2 - Vectorisation batch {i}/{total_batches}")

        # 4) Persist & permissions ----------------------------------------------------
        # db.persist()
        save_progress(100, 100, "2/2 - Sauvegarde vectorstore")

        # Donne les droits d’écriture sur le nouveau vectorstore
        _check_write_permissions(_BUILD_DIR)
        _BUILD_DIR.chmod(0o777)
        for file in _BUILD_DIR.glob("*"):
            file.chmod(0o777)

        _backup_existing_vectorstore()

        # Renomme _BUILD_DIR (nouveau) en VECTORSTORE_DIR (chemin officiel)
        _BUILD_DIR.rename(VECTORSTORE_DIR)
        logging.info("✅ Vectorstore construit et sauvegardé ⟶ %s", VECTORSTORE_DIR)

        # Redonne les permissions sur le nouveau dossier (renommé)
        _check_write_permissions(VECTORSTORE_DIR)
        VECTORSTORE_DIR.chmod(0o777)
        for file in VECTORSTORE_DIR.glob("*"):
            file.chmod(0o777)

        cp.print_success("Répertoire de persistance rechargé avec succès.")
        cp.print_debug(f"Persist directory: {VECTORSTORE_DIR}")


        save_progress(100, 100, "2/2 - Vectorisation terminée")

        return {"status": "success", "message": "Vectorstore sauvegardé avec succès."}

    except PermissionError as exc:
        logging.error("PermissionError: %s", exc)
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        logging.exception("Erreur inattendue")
        return {"status": "error", "message": str(exc)}


if __name__ == "__main__":
    res = build_vectorstore()
    if res["status"] == "success":
        print(res["message"])
    else:
        print(f"❌ {res['message']}")

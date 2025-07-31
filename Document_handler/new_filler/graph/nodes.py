import json
import traceback
from pathlib import Path
import threading
from collections import defaultdict


from ..config import VALID_DIR, REJECTED_DIR, cp
from ..logic.fill_logic import fill_missing_fields, route_document, validate_with_schema
from ..logic.detect_type import detect_document_type
from ..logic.webjson import normalize_entry
from ..logic.load_pdf import process_scraped_pdf_file, process_manual_pdf_file
from ..logic.syllabus import extract_syllabus_structure
from ..preprocessing.update_map import update_output_maps_entry, clean_output_maps, clean_map_files

# Global pour collecter les updates de mapping
_pending_map_updates = defaultdict(list)
_map_update_lock = threading.Lock()

def _atomic_write_json(path, data):
    """Écriture atomique d'un fichier JSON pour éviter les corruptions"""
    import tempfile
    import os
    
    # S'assurer que le dossier parent existe
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Écriture dans un fichier temporaire puis renommage atomique
    with tempfile.NamedTemporaryFile(
        mode='w', 
        encoding='utf-8', 
        dir=path.parent, 
        prefix=f".{path.name}.", 
        suffix='.tmp',
        delete=False
    ) as temp_file:
        try:
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = temp_file.name
        except Exception as e:
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise e
    
    # Renommage atomique
    try:
        if os.name == 'nt':  # Windows
            if path.exists():
                path.unlink()
        os.rename(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e

def log_callback(state, msg, color="white", step_number=None):
    """
    Improved callback with better color usage and step tracking
    """
    file_path = state.get('file_path', 'unknown')
    file_name = Path(file_path).name if file_path != 'unknown' else 'unknown'
    
    # Use appropriate color methods based on message type
    if "ERROR" in msg.upper():
        cp.print_error(f"[{msg}] {file_name}")
    elif "SUCCESS" in msg.upper() or "OK" in msg.upper():
        cp.print_success(f"[{msg}] {file_name}")
    elif "WARNING" in msg.upper():
        cp.print_warning(f"[{msg}] {file_name}")
    elif step_number:
        cp.print_step(f"[{msg}] {file_name}", step_number)
    else:
        # Use the info method for regular messages with colored tags
        if color == "blue":
            cp.print_info(f"[{msg}] {file_name}")
        elif color == "green":
            cp.print_success(f"[{msg}] {file_name}")
        elif color == "red":
            cp.print_error(f"[{msg}] {file_name}")
        elif color == "yellow":
            cp.print_warning(f"[{msg}] {file_name}")
        else:
            cp.print_debug(f"[{msg}] {file_name}")

def log_step_start(state, step_name, step_number=None):
    """Log the start of a processing step"""
    file_name = Path(state.get('file_path', 'unknown')).name
    if step_number:
        cp.print_step(f"Début {step_name} - {file_name}", step_number)
    else:
        cp.print_step(f"Début {step_name} - {file_name}")

def log_step_success(state, step_name, details=None):
    """Log successful completion of a step"""
    file_name = Path(state.get('file_path', 'unknown')).name
    if details:
        cp.print_success(f"✅ {step_name} terminé - {file_name} ({details})")
    else:
        cp.print_success(f"✅ {step_name} terminé - {file_name}")

def log_step_info(state, step_name, info):
    """Log informational message during step processing"""
    file_name = Path(state.get('file_path', 'unknown')).name
    cp.print_info(f"ℹ️  {step_name} - {file_name}: {info}")

def log_processing_stats(state, stats_dict):
    """Log processing statistics"""
    file_name = Path(state.get('file_path', 'unknown')).name
    cp.print_result(f"📊 Statistiques pour {file_name}:")
    for key, value in stats_dict.items():
        cp.print_result(f"   • {key}: {value}")

def api_friendly_wrapper(func):
    """
    Decorator to make functions API-friendly by wrapping them in try-except blocks.
    """
    def wrapper(state):
        try:
            return func(state)
        except Exception as e:
            state["error"] = f"{func.__name__} error: {e}"
            state["traceback"] = traceback.format_exc()
            file_name = Path(state.get('file_path', 'unknown')).name
            cp.print_error(f"❌ ERREUR dans {func.__name__} - {file_name}: {e}")
            return state
    return wrapper

@api_friendly_wrapper
def load_json_node(state):
    log_step_start(state, "Chargement JSON", 1)
    file_path = state["file_path"]
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    state["data"] = data
    log_step_success(state, "Chargement JSON", f"{len(str(data))} caractères")
    return state

@api_friendly_wrapper
def load_pdf_to_data_manual_node(state):
    log_step_start(state, "Traitement PDF manuel", 2)
    pdf_path = state["file_path"]
    result = process_manual_pdf_file(pdf_path)
    if not result:
        raise ValueError("Failed to process PDF")
    state["data"] = result
    log_step_success(state, "Traitement PDF manuel", f"Contenu extrait")
    return state

@api_friendly_wrapper
def load_pdf_to_data_scraped_node(state):
    log_step_start(state, "Traitement PDF scrapé", 2)
    pdf_path = state["file_path"]
    result = process_scraped_pdf_file(pdf_path)
    if not result:
        raise ValueError("Failed to process scraped PDF")
    state["data"] = result
    log_step_success(state, "Traitement PDF scrapé", f"Contenu extrait")
    return state

# pas utilisé dans le graphe actuel,
@api_friendly_wrapper
def detect_type_node(state):
    log_step_start(state, "Détection du type de document", 3)
    content = state["data"].get("content", "")
    doc_type = detect_document_type(content)
    state["data"]["doc_type"] = doc_type
    if "output_data" not in state:
        state["output_data"] = {}
    state["output_data"]["document_type"] = doc_type
    log_step_success(state, "Détection du type", f"Type: {doc_type}")
    return state

@api_friendly_wrapper
def fill_metadata_scraped_node(state):
    log_step_start(state, "Remplissage métadonnées (scrapé)")
    data = state["data"]
    output_data = {
        "document_type": "pdf_scraped",
        "content": data.get("content", ""),
        "metadata": {},
        "source": {
            "chemin_local": data.get("pdf_path", "") or "chemin inconnu",
            "site": data.get("source") or "",
            "url": data.get("metadata", {}).get("url") or ""
        },
        "tags": [],
        "type_specific": {}
    }
    output_data["metadata"]["title"] = data.get("metadata", {}).get("title_2", "")
    output_data["metadata"]["secteur"] = data.get("metadata", {}).get("secteur", "")
    output_data["metadata"]["date"] = data.get("metadata", {}).get("last_modified", "")
    output_data["metadata"]["auteurs"] = data.get("metadata", {}).get("auteurs", [])
    state["output_data"] = output_data
    log_step_success(state, "Métadonnées scrapées", "Structure créée")
    return state

@api_friendly_wrapper
def fill_metadata_manual_node(state):
    log_step_start(state, "Remplissage métadonnées (manuel)")
    data = state["data"]
    output_data = {
        "document_type": "pdf_ajouté_manuellement",
        "content": data.get("content", ""),
        "metadata": {},
        "source": {
            "chemin_local": data.get("pdf_path", "") or "chemin inconnu",
            "site": data.get("source") or "",
            "url": data.get("metadata", {}).get("url") or ""
        },
        "tags": [],
        "type_specific": {}
    }
    output_data["metadata"] = fill_missing_fields(
        data,
        ["title", "secteur", "date", "auteurs", "encadrant", "niveau", "annee", "specialite"],
        "globals/metadata.txt"
    )
    state["output_data"] = output_data
    log_step_success(state, "Métadonnées manuelles", "Champs remplis")
    return state

@api_friendly_wrapper
def fill_tags_node(state):
    data = state["data"]
    output_data = state["output_data"]
    tags_dict = fill_missing_fields(data, ["tags"], "globals/tags.txt")
    output_data["tags"] = tags_dict.get("tags", [])
    state["output_data"] = output_data
    return state

@api_friendly_wrapper
def process_document_node(state):
    log_step_start(state, "Traitement du document")
    data = state["data"]
    updated = route_document(data)
    state["output_data"] = updated
    log_step_success(state, "Traitement document", "Document routé")
    return state

@api_friendly_wrapper
def validate_node(state):
    log_step_start(state, "Validation du document", 4)
    
    if state.get("is_syllabus"):
        state["is_valid"] = bool(state["output_data"].get("specialite", "").strip())
        if not state["is_valid"]:
            state["error"] = "Syllabus specialite is empty"
            cp.print_error(f"❌ Validation échouée: Spécialité syllabus vide - {Path(state.get('file_path', 'unknown')).name}")
        else:
            log_step_success(state, "Validation syllabus", "Spécialité présente")
        return state

    is_valid = validate_with_schema(state["output_data"])
    state["is_valid"] = is_valid
    
    if is_valid:
        log_step_success(state, "Validation schéma", "Document valide")
    else:
        cp.print_error(f"❌ Validation échouée: Document invalide - {Path(state.get('file_path', 'unknown')).name}")
    
    return state

@api_friendly_wrapper
def save_node(state):
    log_step_start(state, "Sauvegarde du document", 5)
    file_path = Path(state["file_path"])
    out_dir = VALID_DIR if state.get("is_valid") else REJECTED_DIR

    if file_path.suffix.lower() == ".pdf":
        out_name = file_path.with_suffix(".json").name
    else:
        out_name = file_path.name

    out_path = out_dir / out_name
    
    # Utilisation de l'écriture atomique pour éviter les corruptions
    try:
        _atomic_write_json(out_path, state["output_data"])
    except Exception as e:
        cp.print_error(f"❌ Erreur lors de la sauvegarde - {file_path.name}: {e}")
        raise
    
    state["out_path"] = str(out_path)
    
    status = "validé" if state.get("is_valid") else "rejeté"
    log_step_success(state, f"Sauvegarde ({status})", f"→ {out_path.name}")
    return state

@api_friendly_wrapper
def save_to_error_node(state):
    file_path = Path(state["file_path"])
    out_name = file_path.with_suffix(".error.json").name
    out_path = REJECTED_DIR / out_name
    
    try:
        _atomic_write_json(out_path, state)
    except Exception as e:
        cp.print_error(f"❌ Erreur lors de la sauvegarde d'erreur - {file_path.name}: {e}")
        # Fallback vers l'écriture normale en cas d'erreur
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    state["out_path"] = str(out_path)
    log_callback(state, f"SAVE TO ERROR: {out_path}", color="red")
    return state

@api_friendly_wrapper
def correction_node(state):
    cp.print_warning(f"⚠️  Correction nécessaire: {Path(state.get('file_path', 'unknown')).name} nécessite une révision manuelle")
    return state

@api_friendly_wrapper
def error_handler_node(state):
    file_name = Path(state.get('file_path', 'unknown')).name
    error_msg = state.get('error', 'Erreur inconnue')
    cp.print_error(f"❌ ERREUR - {file_name}: {error_msg}")
    
    # Show traceback only in debug mode or if specifically requested
    if state.get("show_traceback", False):
        traceback_info = state.get("traceback", "")
        if traceback_info:
            cp.print_debug("Traceback détaillé:")
            cp.print_debug(traceback_info)
    return state

# pas utilisé dans le graphe actuel,
@api_friendly_wrapper
def fill_type_specific_node(state):
    data = state["data"]
    output_data = state["output_data"]
    doc_type = output_data["document_type"]

    if doc_type == "cours":
        output_data["type_specific"]["cours"] = fill_missing_fields(
            data, ["logiciels", "thematique", "resume"], "cours/cours_fields.txt"
        )
    elif doc_type == "administratif":
        output_data["type_specific"]["administratif"] = fill_missing_fields(
            data, ["service", "contact"], "administratif/administratif_fields.txt"
        )
    elif doc_type == "specialite":
        output_data["type_specific"]["specialite"] = fill_missing_fields(
            data, ["departement", "responsable", "description"], "specialite/specialite_fields.txt"
        )
    elif doc_type == "projet":
        output_data["type_specific"]["projet"] = fill_missing_fields(
            data, ["client", "livrable", "techno"], "projet/projet.txt"
        )
    elif doc_type == "infrastructure":
        output_data["type_specific"]["infrastructure"] = fill_missing_fields(
            data, ["adresse", "transports"], "infrastructure/infrastructure_fields.txt"
        )
    elif doc_type == "vie_etudiante":
        output_data["type_specific"]["vie_etudiante"] = fill_missing_fields(
            data, ["activites", "lieux", "evenements"], "vie_etudiante/vie_etudiante_fields.txt"
        )
    state["output_data"] = output_data
    return state

@api_friendly_wrapper
def normalize_json_file_node(state):
    log_step_start(state, "Normalisation JSON")
    file_path = state["file_path"]
    site_name = Path(file_path).parent.parent.name.replace("scraped_", "")
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if isinstance(raw_data, list):
        entries = raw_data
    else:
        entries = [raw_data]

    state["data"] = entries[0] if entries else {}
    normalized = normalize_entry(entries[0], chemin_local=str(file_path), site_name=site_name)
    state["output_data"] = normalized
    log_step_success(state, "Normalisation JSON", f"Site: {site_name}")
    return state

@api_friendly_wrapper
def check_type_of_input_node(state):
    log_step_start(state, "Analyse du type d'entrée")
    file_path = state["file_path"]
    if "data_sites" in file_path:
        state["web_page"] = True
    else:
        state["web_page"] = False

    if file_path.endswith(".pdf") and state["web_page"] == True:
        state["pdf_scraped"] = True
    else:
        state["pdf_scraped"] = False

    if any("syllabus" in part for part in Path(file_path).parts):
        state["is_syllabus"] = True
    else:
        state["is_syllabus"] = False

    info_details = f"web_page={state.get('web_page', False)}, pdf_scraped={state.get('pdf_scraped', False)}, syllabus={state.get('is_syllabus', False)}"
    log_step_success(state, "Analyse type d'entrée", info_details)
    return state

@api_friendly_wrapper
def syllabus_extract_node(state):
    pdf_path = state["file_path"]
    syllabus_json = extract_syllabus_structure(pdf_path)
    state["output_data"] = syllabus_json
    return state

@api_friendly_wrapper
def end_node(state):
    file_name = Path(state.get('file_path', 'unknown')).name
    
    if state.get("is_valid"):
        hash_val = state.get("hash", "")
        input_path = Path(state["file_path"])
        
        # Collecte l'update au lieu de l'écrire immédiatement
        # Cela évite la contention sur les fichiers de mapping
        with _map_update_lock:
            _pending_map_updates[hash_val].append(str(input_path))
        
        # Log processing summary
        stats = {
            "Statut": "✅ Validé et sauvegardé (map en attente)",
            "Fichier de sortie": state.get("out_path", "N/A"),
            "Type de document": state.get("output_data", {}).get("document_type", "N/A")
        }
        log_processing_stats(state, stats)
    else:
        stats = {
            "Statut": "❌ Rejeté",
            "Raison": state.get("error", "Validation échouée"),
            "Fichier de sortie": state.get("out_path", "N/A")
        }
        log_processing_stats(state, stats)

    cp.print_result(f"🏁 Traitement terminé pour {file_name}")
    cp.print_separator()
    return state

def flush_pending_map_updates():
    """Écrit toutes les updates en attente de manière sécurisée"""
    global _pending_map_updates
    
    with _map_update_lock:
        updates_to_process = dict(_pending_map_updates)
        _pending_map_updates.clear()
    
    if not updates_to_process:
        cp.print_info("📝 Aucune mise à jour de map en attente")
        return
    
    cp.print_info(f"📝 Mise à jour des maps pour {len(updates_to_process)} fichiers...")
    
    # Traite les updates une par une avec protection FileLock
    success_count = 0
    error_count = 0
    
    for hash_val, paths in updates_to_process.items():
        for path in paths:
            try:
                update_output_maps_entry(hash_val, path)
                success_count += 1
            except Exception as e:
                cp.print_error(f"❌ Erreur mise à jour map pour {path}: {e}")
                error_count += 1
    
    # Nettoyage final avec protection
    try:
        clean_output_maps()
        clean_map_files()
        if error_count == 0:
            cp.print_success(f"✅ Maps mises à jour avec succès: {success_count} fichiers traités")
        else:
            cp.print_warning(f"⚠️  Maps mises à jour: {success_count} succès, {error_count} erreurs")
    except Exception as e:
        cp.print_error(f"❌ Erreur lors du nettoyage des maps: {e}")

def get_pending_updates_count():
    """Retourne le nombre d'updates en attente"""
    with _map_update_lock:
        return sum(len(paths) for paths in _pending_map_updates.values())

def clear_pending_updates():
    """Vide les updates en attente (pour les cas d'erreur)"""
    global _pending_map_updates
    with _map_update_lock:
        _pending_map_updates.clear()
    cp.print_info("🧹 Updates de mapping en attente supprimées")
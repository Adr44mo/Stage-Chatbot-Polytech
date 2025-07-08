import json
import traceback
from pathlib import Path
from ..config import VALID_DIR, REJECTED_DIR
from ..logic.fill_logic import fill_missing_fields, route_document, validate_with_schema
from ..logic.detect_type import detect_document_type
from ..logic.webjson import normalize_entry
from ..logic.load_pdf import process_scraped_pdf_file, process_manual_pdf_file
from ..logic.syllabus import extract_syllabus_structure

def log_callback(state, msg):
    print(f"[{msg}] {state.get('file_path', '')}")

def load_json_node(state):
    file_path = state["file_path"]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        state["data"] = data
        log_callback(state, "LOAD")
        return state
    except Exception as e:
        state["error"] = f"Load error: {e}"
        state["traceback"] = traceback.format_exc()
        raise

def load_pdf_to_data_manual_node(state):
    pdf_path = state["file_path"]
    result = process_manual_pdf_file(pdf_path)
    if not result:
        state["error"] = "Failed to process PDF"
        return state
    state["data"] = result
    log_callback(state, "LOAD_PDF_MANUAL")
    return state

def load_pdf_to_data_scraped_node(state):
    pdf_path = state["file_path"]
    result = process_scraped_pdf_file(pdf_path)
    if not result:
        state["error"] = "Failed to process scraped PDF"
        return state
    state["data"] = result
    log_callback(state, "LOAD_PDF_SCRAPED")
    return state

def detect_type_node(state):
    try:
        content = state["data"].get("content", "")
        doc_type = detect_document_type(content)
        state["data"]["doc_type"] = doc_type
        if "output_data" not in state:
            state["output_data"] = {}
        state["output_data"]["document_type"] = doc_type        
        log_callback(state, f"DETECT_TYPE: {doc_type}")
        return state
    except Exception as e:
        state["error"] = f"Detect type error: {e}"
        state["traceback"] = traceback.format_exc()
        log_callback(state, "DETECT_TYPE ERROR")
        raise

def fill_metadata_scraped_node(state):
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
    # Fill metadata for scraped
    output_data["metadata"]["title"] = data.get("metadata", {}).get("title_2", "")
    output_data["metadata"]["secteur"] = data.get("metadata", {}).get("secteur", "")
    output_data["metadata"]["date"] = data.get("metadata", {}).get("last_modified", "")
    output_data["metadata"]["auteurs"] = data.get("metadata", {}).get("auteurs", [])
    state["output_data"] = output_data
    log_callback(state, "FILL_METADATA_SCRAPED")
    return state

def fill_metadata_manual_node(state):
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
    # Fill metadata for manual
    output_data["metadata"] = fill_missing_fields(
        data,
        ["title", "secteur", "date", "auteurs", "encadrant", "niveau", "annee", "specialite"],
        "globals/metadata.txt"
    )
    state["output_data"] = output_data
    log_callback(state, "FILL_METADATA_MANUAL")
    return state

def fill_tags_node(state):
    data = state["data"]
    output_data = state["output_data"]
    tags_dict = fill_missing_fields(data, ["tags"], "globals/tags.txt")
    output_data["tags"] = tags_dict.get("tags", [])
    state["output_data"] = output_data
    return state

def process_document_node(state):
    try:
        data = state["data"]
        updated = route_document(data)
        state["output_data"] = updated
        log_callback(state, "PROCESS")
        return state
    except Exception as e:
        state["error"] = f"Process error: {e}"
        state["traceback"] = traceback.format_exc()
        raise

def validate_node(state):
    #dans le cas des syllabus, on valide si specialite est non vide
    if state.get("is_syllabus"):
        state["is_valid"] = bool(state["output_data"].get("specialite", "").strip())
        if not state["is_valid"]:
            state["error"] = "Syllabus specialite is empty"
            log_callback(state, f"VALIDATE SYLLABUS EMPTY")
        else:
            log_callback(state, f"VALIDATE SYLLABUS OK")
        return state

    try:
        is_valid = validate_with_schema(state["output_data"])
        state["is_valid"] = is_valid
        #print(f"[OUTPUT_DATA] {json.dumps(state.get('output_data', {}), ensure_ascii=False, indent=2)}")
        return state
    except Exception as e:
        state["error"] = f"Validation error: {e}"
        state["traceback"] = traceback.format_exc()
        raise

def save_node(state):
    try:
        file_path = Path(state["file_path"])
        out_dir = VALID_DIR if state.get("is_valid") else REJECTED_DIR
        
        # If the input is a PDF, change the output extension to .json
        if file_path.suffix.lower() == ".pdf":
            out_name = file_path.with_suffix(".json").name
        else:
            out_name = file_path.name

        out_path = out_dir / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(state["output_data"], f, ensure_ascii=False, indent=2)
        state["out_path"] = str(out_path)
        log_callback(state, f"SAVE: {out_path}")
        return state
    except Exception as e:
        state["error"] = f"Save error: {e}"
        state["traceback"] = traceback.format_exc()
        raise

def save_to_error_node(state):
    """
    Node to save the state to an error file in the REJECTED_DIR.
    """
    try:
        file_path = Path(state["file_path"])
        out_name = file_path.with_suffix(".error.json").name
        out_path = REJECTED_DIR / out_name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        state["out_path"] = str(out_path)
        log_callback(state, f"SAVE TO ERROR: {out_path}")
        return state
    except Exception as e:
        print(f"[ERROR] Failed to save to error: {e}")
        return state



def correction_node(state):
    print(f"[CORRECTION] Document {state.get('file_path')} needs correction or manual review.")
    return state

def error_handler_node(state):
    print(f"[❌ ERROR] {state.get('file_path')}: {state.get('error')}")
    print(state.get("traceback", ""))
    return state

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

def normalize_json_file_node(state):
    """
    Node for the graph: takes a state with 'file_path', loads and normalizes the JSON,
    and returns the normalized JSON in state['output_data'].
    """
    file_path = state["file_path"]
    site_name = Path(file_path).parent.parent.name.replace("scraped_", "")
    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Handle both list and dict
    if isinstance(raw_data, list):
        entries = raw_data
    else:
        entries = [raw_data]

    # Store raw data in state for further processing, the data need to be in json format
    state["data"] = entries[0] if entries else {}
    # For a single file, you can choose to return the first normalized entry,
    # or all as a list. Here, we return the first (adapt as needed):
    normalized = normalize_entry(entries[0], chemin_local=str(file_path), site_name=site_name)
    state["output_data"] = normalized
    log_callback(state, "NORMALIZE_JSON_FILE")
    return state

def check_type_of_input_node(state):
    """
    Node to check if the input is a web page or a PDF/JSON file.
    Sets 'web_page' to True if it's a web page, False otherwise.
    """
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

    log_callback(state, f"CHECK_TYPE_OF_INPUT: web_page={state.get('web_page', False)}, pdf_scraped={state.get('pdf_scraped', False)}, is_syllabus={state.get('is_syllabus', False)}")
    return state


def syllabus_extract_node(state):
    pdf_path = state["file_path"]
    syllabus_json = extract_syllabus_structure(pdf_path)
    state["output_data"] = syllabus_json
    return state
import json
import re
from pathlib import Path
from jsonschema import validate, ValidationError
from ..logic.detect_type import detect_document_type
from ..utils.ollama_wrapper import ask_model
from ..config import PROMPTS_DIR, SCHEMA

def validate_with_schema(data):
    try:
        validate(instance=data, schema=SCHEMA)
        return True
    except ValidationError as e:
        print(f"[❌ Validation error] {e.message}")
        return False

def extract_json(response):
    match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
    if not match:
        match = re.search(r"(\{.*\})", response, re.DOTALL)
    if not match:
        raise ValueError("Aucun JSON trouvé dans la réponse")
    raw_json = match.group(1)
    cleaned = re.sub(r"//.*", "", raw_json)
    return json.loads(cleaned)

def fill_missing_fields(data: dict, fields: list, prompt_file: str):
    prompt_path = PROMPTS_DIR / prompt_file
    formatted_data = json.dumps(data, ensure_ascii=False, indent=2)
    prompt = prompt_path.read_text(encoding="utf-8").replace("{{data}}", formatted_data[:20000])
    response = ask_model(prompt)
    try:
        values = extract_json(response)
        return {f: values[f] for f in fields if f in values}
    except Exception as e:
        print(f"[WARN] Erreur parsing : {e}")
        print(f"[RESPONSE] {response}")
        return {}

def route_document(data):
    content = data.get("content", "")
    output_data = {
        "document_type": detect_document_type(content),
        "content": content,
        "metadata": {},
        "source": {
            "chemin_local": data.get("pdf_path", "") or "chemin inconnu",
            "site": data.get("source") or "",
            "url": data.get("metadata", {}).get("url") or ""
        },
        "tags": [],
        "type_specific": {}
    }
    # Fill metadata
    if str(output_data["source"].get("site", "")).startswith("scraped_"):
        output_data["metadata"]["title"] = data.get("metadata", {}).get("title_2", "")
        output_data["metadata"]["secteur"] = data.get("metadata", {}).get("secteur", "")
        output_data["metadata"]["date"] = data.get("metadata", {}).get("last_modified", "")
        output_data["metadata"]["auteurs"] = data.get("metadata", {}).get("auteurs", [])
    else:
        output_data["metadata"] = fill_missing_fields(
            data,
            ["title", "secteur", "date", "auteurs", "encadrant", "niveau", "annee", "specialite"],
            "globals/metadata.txt"
        )
    tags_dict = fill_missing_fields(data, ["tags"], "globals/tags.txt")
    output_data["tags"] = tags_dict.get("tags", [])
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
    return output_data
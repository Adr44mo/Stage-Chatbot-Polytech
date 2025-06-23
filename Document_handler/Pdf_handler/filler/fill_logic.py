import json
import re
from pathlib import Path
from .utils.ollama_wrapper import ask_model
from .handlers.detect_type import detect_document_type

PROMPTS_DIR = Path(__file__).parent / "prompts"

def extract_json(response):
    # Essaie d'extraire un bloc JSON entre ``` ou simplement le premier objet JSON
    match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
    if not match:
        # Fallback : cherche un objet JSON sans ``` blocs
        match = re.search(r"(\{.*\})", response, re.DOTALL)
    if not match:
        raise ValueError("Aucun JSON trouvé dans la réponse")

    raw_json = match.group(1)

    # Supprime les commentaires `//`
    cleaned = re.sub(r"//.*", "", raw_json)

    return json.loads(cleaned)

def fill_missing_fields(data: dict, fields: list, prompt_file: str):
    prompt_path = PROMPTS_DIR / prompt_file

    # Formattage JSON de l'entrée complète
    formatted_data = json.dumps(data, ensure_ascii=False, indent=2)
    prompt = prompt_path.read_text(encoding="utf-8").replace("{{data}}", formatted_data[:20000])
    
    #print(f"[DEBUG] le prompt d'entrée {prompt}")

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
            "url": data["metadata"].get("url") or ""
        },
        "tags": {},
        "type_specific": {}
    }

    print(f"[DEBUG] document_type détecté : {output_data['document_type']}")

    # Champs globaux
    if str(output_data["source"].get("site", "")).startswith("scraped_"):
        print("[DEBUG] Source détectée comme provenant d'un scraping.")
        output_data["metadata"]["title"] = data["metadata"].get("title_2", "")
        output_data["metadata"]["secteur"] = data["metadata"].get("secteur", "")
        output_data["metadata"]["date"] = data["metadata"].get("last_modified", "")
        output_data["metadata"]["auteurs"] = data["metadata"].get("auteurs", [])

    else:
        output_data["metadata"] = fill_missing_fields(data,
            ["title", "secteur", "date", "auteurs", "encadrant", "niveau", "annee", "specialite"],
            "globals/metadata.txt")

    tags_dict = fill_missing_fields(data, ["tags"], "globals/tags.txt")
    output_data["tags"] = tags_dict.get("tags", [])

    # Champs spécifiques
    doc_type = output_data["document_type"]
    if doc_type == "cours":
        output_data["type_specific"]["cours"] = fill_missing_fields(data,
            ["logiciels", "thematique", "resume"],
            "cours/cours_fields.txt")
    elif doc_type == "administratif":
        output_data["type_specific"]["administratif"] = fill_missing_fields(data,
            ["service", "contact"],
            "administratif/administratif_fields.txt")
    elif doc_type == "specialite":
        output_data["type_specific"]["specialite"] = fill_missing_fields(data,
            ["departement", "responsable", "description"],
            "specialite/specialite_fields.txt")
    elif doc_type == "projet":
        output_data["type_specific"]["projet"] = fill_missing_fields(data,
            ["client", "livrable", "techno"],
            "projet/projet.txt")
    elif doc_type == "infrastructure":
        output_data["type_specific"]["infrastructure"] = fill_missing_fields(data,
            ["adresse", "transports"],
            "infrastructure/infrastructure_fields.txt")
    elif doc_type == "vie_etudiante":
        output_data["type_specific"]["vie_etudiante"] = fill_missing_fields(data,
            ["activites", "lieux", "evenements"],
            "vie_etudiante/vie_etudiante_fields.txt")
    elif doc_type == "specialite":
        output_data["type_specific"]["specialite"] = fill_missing_fields(data,
            ["departement", "responsable"],
            "specialite/specialite_fields.txt")

    return output_data


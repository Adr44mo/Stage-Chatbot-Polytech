from ..utils.ollama_wrapper import ask_model
import json

def detect_document_type(content: str) -> str:
    prompt = f"""
Voici un extrait d’un document :

{content[:2000]}

À partir de ce contenu, quel est le type de document parmi les suivants : 
- cours
- projet
- administratif
- specialite
- vie_etudiante
- infrastructure

Réponds uniquement par une des valeurs attendues au format JSON : {{ "document_type": "..." }}
"""
    response = ask_model(prompt)

    try:
        parsed = json.loads(response)
        doc_type = parsed.get("document_type", "").lower().strip()
        if doc_type in {"cours", "projet", "administratif", "specialite", "vie_etudiante", "infrastructure"}:
            return doc_type
    except Exception:
        print(f"[⚠️] Erreur de parsing dans detect_type: {response}")
    
    raise ValueError("Impossible de déterminer automatiquement le type de document.")

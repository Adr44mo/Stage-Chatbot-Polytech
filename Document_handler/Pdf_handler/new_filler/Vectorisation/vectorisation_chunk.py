import os
import json
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from ..logic.chunck_syll import chunk_syllabus_for_rag
from ..config import OPENAI_API_KEY, VALID_DIR

# Paths
NORMALIZED_DIR = VALID_DIR
VECTORSTORE_DIR = Path(__file__).parent / "vectorstore_Syllabus"

# Load all normalized JSON documents
def load_normalized_docs():
    docs = []
    for json_file in NORMALIZED_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                doc = json.load(f)
                docs.append(doc)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSONDecodeError in {json_file.name}: {e}")
        except Exception as e:
            print(f"⚠️ Unexpected error in {json_file.name}: {type(e).__name__} - {e}")
    return docs
# loads the syllabus thar are in children dir of validated dir
def load_syllabus_docs():
    syllabus_docs = []
    for json_file in NORMALIZED_DIR.glob("**/syllabus*.json*"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                doc = json.load(f)
                syllabus_docs.append(doc)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSONDecodeError in {json_file.name}: {e}")
        except Exception as e:
            print(f"⚠️ Unexpected error in {json_file.name}: {type(e).__name__} - {e}")
    return syllabus_docs

# Convert normalized docs to LangChain Document objects
def convert_to_documents(raw_docs):
    lc_docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    for doc in raw_docs:
        content = doc.get("content", "")
        if not content.strip():
            continue  # Ignore les documents sans contenu

        # Vérifier et normaliser la structure selon le schéma polytech
        normalized_doc = ensure_polytech_structure(doc)

        # Métadonnées à plat uniquement (pas de dict imbriqué)
        metadata_raw = normalized_doc.copy()
        metadata_raw.pop("content", None)

        # Aplatir les objets complexes comme "source" ou "metadata"
        flat_metadata = {}
        for key, value in metadata_raw.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_metadata[f"{key}.{sub_key}"] = str(sub_value)
            elif isinstance(value, list):
                flat_metadata[key] = ", ".join(map(str, value))
            else:
                flat_metadata[key] = str(value)

        # Split + assign
        chunks = splitter.split_text(content)
        for chunk in chunks:
            lc_docs.append(Document(page_content=chunk, metadata=flat_metadata))

    return lc_docs


def ensure_polytech_structure(doc):
    """
    S'assure que le document respecte la structure du schéma polytech
    """
    # Si le document est déjà bien structuré, le retourner tel quel
    if (doc.get("document_type") and 
        doc.get("metadata") and 
        doc.get("source") and 
        "chemin_local" in doc.get("source", {})):
        return doc
    
    # Sinon, tenter de normaliser
    normalized = {
        "document_type": doc.get("document_type", "page_web"),
        "metadata": {
            "title": doc.get("metadata", {}).get("title", doc.get("title", ""))
        },
        "source": {
            "category": doc.get("source", {}).get("category", "scrapping"),
            "chemin_local": doc.get("source", {}).get("chemin_local", ""),
        },
        "content": doc.get("content", ""),
        "tags": doc.get("tags", [])
    }
    
    # Ajouter l'URL si disponible
    if doc.get("source", {}).get("url"):
        normalized["source"]["url"] = doc["source"]["url"]
    
    # Ajouter le site si disponible
    if doc.get("source", {}).get("site"):
        normalized["source"]["site"] = doc["source"]["site"]
    
    return normalized


def syllabus_to_langchain_documents(syllabus_data):
    """
    Transforme les syllabus directement en objets Document Langchain
    en utilisant la même logique d'aplatissement que convert_to_documents
    """
    # D'abord, chunker le syllabus en documents compatibles
    syllabus_docs = chunk_syllabus_for_rag(syllabus_data)
    
    # Ensuite, convertir ces documents en objets Document Langchain
    lc_docs = []
    
    for doc in syllabus_docs:
        content = doc.get("content", "")
        if not content.strip():
            continue
        
        # Utiliser la même logique d'aplatissement que convert_to_documents
        # Normaliser la structure selon le schéma polytech
        normalized_doc = ensure_polytech_structure(doc)
        
        # Aplatir les métadonnées comme dans convert_to_documents
        metadata_raw = normalized_doc.copy()
        metadata_raw.pop("content", None)
        
        flat_metadata = {}
        
        # Traiter les tags spécifiquement si présents (comme chaîne de caractères)
        if "tags" in metadata_raw and isinstance(metadata_raw["tags"], list):
            flat_metadata["tags"] = ", ".join(metadata_raw["tags"])
            metadata_raw.pop("tags")
        
        # Continuer avec l'aplatissement standard
        for key, value in metadata_raw.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_metadata[f"{key}.{sub_key}"] = str(sub_value)
            elif isinstance(value, list):
                flat_metadata[key] = ", ".join(map(str, value))
            else:
                flat_metadata[key] = str(value)
        
        # Créer un Document Langchain (pas besoin de splitter davantage)
        lc_docs.append(Document(page_content=content, metadata=flat_metadata))
    
    return lc_docs


def main(VECTORSTORE_DIR=VECTORSTORE_DIR):
    print("📄 Chargement des documents JSON normalisés...")
    raw_docs = load_normalized_docs()
    print(f"✅ {len(raw_docs)} documents chargés.")

    # Traiter les documents normalisés
    print("✂️ Découpage des documents normalisés en chunks...")
    lc_documents = convert_to_documents(raw_docs)
    print(f"✅ {len(lc_documents)} chunks créés pour les documents normalisés.")

    # Traiter les syllabus séparément
    print("📚 Chargement et traitement des syllabus...")
    syllabus_data = load_syllabus_docs()
    if syllabus_data:
        syllabus_lc_docs = syllabus_to_langchain_documents(syllabus_data)
        print(f"✅ {len(syllabus_lc_docs)} chunks créés pour les syllabus.")
        
        # Combiner les deux ensembles de Documents
        lc_documents.extend(syllabus_lc_docs)
        print(f"✅ Total: {len(lc_documents)} chunks.")
    else:
        print("⚠️ Aucun syllabus trouvé.")

    print("🔗 Génération des embeddings avec OpenAI...")
    embeddings = OpenAIEmbeddings()

    print(f"💾 Sauvegarde dans ChromaDB → {VECTORSTORE_DIR}")
    db = Chroma.from_documents(lc_documents, embedding=embeddings, persist_directory=str(VECTORSTORE_DIR))
    print("✅ Vectorstore sauvegardée.")

if __name__ == "__main__":
    main(VECTORSTORE_DIR)

# python -m new_filler.Vectorisation.vectorisation_chunk
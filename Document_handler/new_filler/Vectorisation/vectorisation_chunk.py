import os
import json
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from ..logic.chunck_syll import chunk_syllabus_for_rag
from ..config import OPENAI_API_KEY, VALID_DIR
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Paths
NORMALIZED_DIR = VALID_DIR
VECTORSTORE_DIR = Path(__file__).parent / "vectorstore_Syllabus"

# Load all normalized JSON documents except syllabus files
def load_normalized_docs():
    docs = []
    for json_file in NORMALIZED_DIR.glob("*.json"):
        # Ignore files that look like syllabus files
        if "syllabus" in json_file.name:
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                doc = json.load(f)
                docs.append(doc)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSONDecodeError in {json_file.name}: {e}")
        except Exception as e:
            print(f"⚠️ Unexpected error in {json_file.name}: {type(e).__name__} - {e}")
    return docs
# loads the syllabus that are in children dir of validated dir
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
    
    # Debug: afficher la taille totale des chunks syllabus
    """
    total_chars = sum(len(doc.page_content) for doc in lc_docs)
    if lc_docs:
        chunk_lengths = [len(doc.page_content) for doc in lc_docs]
        min_len = min(chunk_lengths)
        max_len = max(chunk_lengths)
        avg_len = total_chars / len(lc_docs)
        print(f"🪓 syllabus_to_langchain_documents: {len(lc_docs)} chunks, taille totale = {total_chars} caractères")
        print(f"   ➡️ Taille min: {min_len}, max: {max_len}, moyenne: {avg_len:.2f} caractères")
        # Affiche la taille des 10 plus gros chunks et leur contenu
        top_chunks = sorted(lc_docs, key=lambda d: len(d.page_content), reverse=True)[:10]
        print("   ➡️ Top 10 des plus gros chunks :")
        for idx, doc in enumerate(top_chunks, 1):
            print(f"     {idx}. Taille: {len(doc.page_content)} caractères")
            print(f"        Contenu: {doc.page_content[:500]}{'...' if len(doc.page_content) > 500 else ''}")
    else:
        print("🪓 syllabus_to_langchain_documents: 0 chunk")
    """
    return lc_docs

def sup_old_vectorstore(VECTORSTORE_DIR=VECTORSTORE_DIR):
    """
    Supprime l'ancien vectorstore s'il existe et crée une sauveguarde du précédent.
    """
    if VECTORSTORE_DIR.exists():
        backup_dir = VECTORSTORE_DIR.parent / "vectorstore_backup"
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
        for file in VECTORSTORE_DIR.glob("*"):
            file.rename(backup_dir / file.name)
        print(f"✅ Ancien vectorstore sauvegardé dans {backup_dir}")
    else:
        print("⚠️ Aucun ancien vectorstore à supprimer.")
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Nouveau vectorstore créé à {VECTORSTORE_DIR}")

def add_write_and_read_permissions(VECTORSTORE_DIR=VECTORSTORE_DIR):
    """
    Ajoute les permissions de lecture et d'écriture pour le vectorstore et tout les sous dossiers/fichiers.
    """
    if VECTORSTORE_DIR.exists():
        VECTORSTORE_DIR.chmod(0o777)  # Permissions de lecture, écriture et exécution pour le répertoire
        print(f"✅ Permissions de lecture et écriture ajoutées pour {VECTORSTORE_DIR}")
        for file in VECTORSTORE_DIR.glob("*"):
            file.chmod(0o777)  # Permissions de lecture et écriture pour tous les utilisateurs
            print(f"✅ Permissions de lecture et écriture ajoutées pour {file}")
    else:
        print(f"⚠️ Le répertoire {VECTORSTORE_DIR} n'existe pas.")

def split_into_batches(data, batch_size):
    """
    Divise une liste en plusieurs lots de taille batch_size.
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


def check_write_permissions(directory):
    """
    Vérifie si le répertoire est accessible en écriture. ainsi que le fichier sqlite3
    """
    if not os.access(directory, os.W_OK):
        raise PermissionError(f"Le répertoire {directory} n'est pas accessible en écriture.")
    print(f"Vérification des permissions pour le répertoire {directory}...")
    if (directory / "chroma.sqlite3").exists():
        print(f"Vérification des permissions pour le fichier chroma.sqlite3 dans {directory}...")
        if not os.access(directory / "chroma.sqlite3", os.W_OK):
            raise PermissionError(f"Le fichier chroma.sqlite3 dans {directory} n'est pas accessible en écriture.")
    print(f"✅ Permissions de lecture et écriture vérifiées pour {directory} et chroma.sqlite3.")


def main(VECTORSTORE_DIR=VECTORSTORE_DIR):
    try:

        VECTORSTORE_DIR_BUILD = VECTORSTORE_DIR.parent / "vectorstore_Syllabus_Construct"

        VECTORSTORE_DIR_BUILD.mkdir(parents=True, exist_ok=True)

        check_write_permissions(VECTORSTORE_DIR_BUILD)
        logging.info("🔧 Initialisation du vectorstore...")

        logging.info("📄 Chargement des documents JSON normalisés...")
        raw_docs = load_normalized_docs()
        logging.info(f"✅ {len(raw_docs)} documents chargés.")

        # Traiter les documents normalisés
        logging.info("✂️ Découpage des documents normalisés en chunks...")
        lc_documents = convert_to_documents(raw_docs)
        logging.info(f"✅ {len(lc_documents)} chunks créés pour les documents normalisés.")

        # Traiter les syllabus séparément
        logging.info("📚 Chargement et traitement des syllabus...")
        syllabus_data = load_syllabus_docs()
        if syllabus_data:
            syllabus_lc_docs = syllabus_to_langchain_documents(syllabus_data)
            logging.info(f"✅ {len(syllabus_lc_docs)} chunks créés pour les syllabus.")

            # Combiner les deux ensembles de Documents
            lc_documents.extend(syllabus_lc_docs)
            logging.info(f"✅ Total: {len(lc_documents)} chunks.")
        else:
            logging.warning("⚠️ Aucun syllabus trouvé.")

        logging.info("🔗 Génération des embeddings avec OpenAI...")
        embeddings = OpenAIEmbeddings()

        logging.info(f"💾 Sauvegarde dans ChromaDB → {VECTORSTORE_DIR_BUILD}")

        # Vérifier les permissions d'écriture pour le répertoire
        check_write_permissions(VECTORSTORE_DIR_BUILD)

        # Diviser les documents en lots
        BATCH_SIZE = 200
        batches = list(split_into_batches(lc_documents, BATCH_SIZE))

        # Créer la base avec le premier batch
        if batches:
            first_batch = batches[0]
            logging.info(f"Création de la base avec le premier lot contenant {len(first_batch)} documents...")
            db = Chroma.from_documents(first_batch, embedding=embeddings, persist_directory=str(VECTORSTORE_DIR_BUILD))
            
            # Ajouter les batches suivants à la base existante
            for batch_num, batch in enumerate(batches[1:], start=2):
                try:
                    logging.info(f"Ajout du lot {batch_num}/{len(batches)} contenant {len(batch)} documents...")
                    db.add_documents(batch)
                except PermissionError as e:
                    logging.error(f"Erreur de permission lors du traitement du lot {batch_num}: {e}")
                    return {"status": "error", "message": f"Erreur de permission: {e}"}
                except Exception as e:
                    logging.error(f"Erreur lors du traitement du lot {batch_num}: {e}")
                    return {"status": "error", "message": f"Erreur lors du traitement du lot {batch_num}: {e}"}
        else:
            logging.warning("Aucun document à traiter !")
            return {"status": "error", "message": "Aucun document à traiter"}

        add_write_and_read_permissions(VECTORSTORE_DIR_BUILD)

        # Sauvegarder VECTORSTORE_DIR avant de le remplacer
        if VECTORSTORE_DIR.exists():
            backup_dir = VECTORSTORE_DIR.parent / "vectorstore_backup"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"vectorstore_backup_{timestamp}"
            VECTORSTORE_DIR.rename(backup_path)
            logging.info(f"✅ VECTORSTORE_DIR sauvegardé dans {backup_path}")

        # Remlacer le répertoire de construction par le répertoire final
        if VECTORSTORE_DIR_BUILD.exists():
            VECTORSTORE_DIR_BUILD.rename(VECTORSTORE_DIR)
            logging.info("✅ VECTORSTORE_DIR_BUILD renommé en VECTORSTORE_DIR.")

        logging.info("✅ Vectorstore sauvegardée.")
        return {"status": "success", "message": "Vectorstore sauvegardée avec succès."}

    except PermissionError as e:
        logging.error(f"Erreur de permission: {e}")
        return {"status": "error", "message": f"Erreur de permission: {e}"}
    except Exception as e:
        logging.error(f"Erreur dans le processus principal: {e}")
        return {"status": "error", "message": f"Erreur dans le processus principal: {e}"}

# python -m new_filler.Vectorisation.vectorisation_chunk

if __name__ == "__main__":

    #result = main(VECTORSTORE_DIR)
    #if result["status"] == "success":
    #    print(result["message"])
    #else:
    #    print(f"❌ {result['message']}")
    add_write_and_read_permissions(VECTORSTORE_DIR=VECTORSTORE_DIR)
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# Paths
NORMALIZED_DIR = Path(__file__).parent.parent / "Corpus" / "json_normalized" / "validated"
VECTORSTORE_DIR = Path(__file__).parent / "vectorstore"

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


# Convert normalized docs to LangChain Document objects
def convert_to_documents(raw_docs):
    lc_docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    for doc in raw_docs:
        content = doc.get("content", "")
        if not content.strip():
            continue  # Ignore les documents sans contenu

        # Métadonnées à plat uniquement (pas de dict imbriqué)
        metadata_raw = doc.copy()
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


def main(VECTORSTORE_DIR=VECTORSTORE_DIR):
    print("📄 Chargement des documents JSON normalisés...")
    raw_docs = load_normalized_docs()
    print(f"✅ {len(raw_docs)} documents chargés.")

    print("✂️ Découpage en chunks...")
    lc_documents = convert_to_documents(raw_docs)
    print(f"✅ {len(lc_documents)} chunks créés.")

    print("🔗 Génération des embeddings avec OpenAI...")
    embeddings = OpenAIEmbeddings()

    print(f"💾 Sauvegarde dans ChromaDB → {VECTORSTORE_DIR}")
    db = Chroma.from_documents(lc_documents, embedding=embeddings, persist_directory=str(VECTORSTORE_DIR))
    db.persist()
    print("✅ Vectorstore sauvegardée.")

if __name__ == "__main__":
    main(VECTORSTORE_DIR)

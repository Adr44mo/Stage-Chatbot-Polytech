import os
import yaml
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import configs

# Charger la configuration YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Obtenir le modèle sélectionné
MODEL_CHOICE = "gpt-4o-mini"
selected_model = config["llm"].get(MODEL_CHOICE)
llm_config = config["llm"][selected_model]

def load_all_pdfs_from_directory(directory_path):
    pdf_documents = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                print(f"📄 Ajout du fichier PDF : {file}")  # Affiche le nom du fichier PDF ajouté
                loader = PyPDFLoader(file_path)
                pdf_documents.extend(loader.load())
    return pdf_documents

def create_embeddings():
    directory_path = os.path.abspath("corpus_v1.3/pdf")
    docs = load_all_pdfs_from_directory(directory_path)

    # Diviser les documents en petits segments
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)

    # Sélection des embeddings en fonction du modèle LLM
    if llm_config["embeddings"] == "OpenAIEmbeddings":
        embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
    elif llm_config["embeddings"] == "OllamaEmbeddings":
        from langchain_community.embeddings import OllamaEmbeddings
        embeddings = OllamaEmbeddings(model_name="llama3")

    # Création des embeddings et indexation avec FAISS
    vector = FAISS.from_documents(documents, embeddings)

    # Sauvegarde de l'index FAISS
    vector.save_local("faiss_index")
    print(f"✅ Index FAISS créé et sauvegardé pour `{selected_model}`.")

# Appeler la fonction principale
create_embeddings()

import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
import configs
import yaml

# Charger la configuration YAML avec un chemin absolu
def load_config():
    # Récupérer le chemin absolu de la racine du projet
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(project_root, "config.yaml")

    # Vérifier si le fichier existe
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"❌ Le fichier config.yaml est introuvable à : {yaml_path}")

    # Charger le fichier YAML
    with open(yaml_path, "r") as file:
        return yaml.safe_load(file)

def load_all_pdfs_from_directory(directory_path):
    pdf_documents = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".pdf"):
                file_path = os.path.join(root, file)
                print(f"Ajout du fichier PDF : {file}")  # Affiche le nom du fichier PDF ajouté
                loader = PyPDFLoader(file_path)
                pdf_documents.extend(loader.load())
    return pdf_documents


# Fonction pour créer des embeddings dynamiquement en fonction du modèle sélectionné
def create_embeddings(model_name, embeddings_type, faiss_index_path):
    directory_path = os.path.abspath("../../corpus_v1.3/pdf")
    docs = load_all_pdfs_from_directory(directory_path)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)

    # Sélectionner automatiquement le type d'embeddings
    if embeddings_type == "OpenAIEmbeddings":
        embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
    elif embeddings_type == "OllamaEmbeddings":
        embeddings = OllamaEmbeddings(model=model_name)
    else:
        raise ValueError(f"🚨 Type d'embedding inconnu : {embeddings_type}")

    # Création et sauvegarde de l'index FAISS
    vector = FAISS.from_documents(documents, embeddings)
    faiss_index_path = os.path.abspath(faiss_index_path)
    vector.save_local(faiss_index_path)

    print(f"✅ Index FAISS créé et sauvegardé dans : {faiss_index_path}")





if __name__ == "__main__":
    config = load_config()
    selected_model = config["llm"]["default_model"]
    model_config = config["llm"].get(selected_model)

    embeddings_type = model_config["embeddings"]
    faiss_index_path = model_config["faisspath"]

    faiss_index_path = f"../{faiss_index_path}"

    print(f"✅ Fichier config.yaml chargé avec succès. Modèle sélectionné : {selected_model}")

    # 🔹 Exécuter la création des embeddings en fonction du modèle sélectionné
    print(f"🔍 Utilisation des embeddings {embeddings_type} pour {selected_model}...")
    create_embeddings(selected_model, embeddings_type, faiss_index_path)



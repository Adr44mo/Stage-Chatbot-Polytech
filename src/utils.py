# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import os
import yaml

# Imports d'elements specifiques externes
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import de variables (cle api)
from keys_file import OPENAI_API_KEY

# ------------------------------------------------------------------
# Fonction pour charger une configuration yaml avec un chemin absolu
# ------------------------------------------------------------------

def load_config():

    # Recuperation du chemin absolu de la racine du projet
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yaml_path = os.path.join(project_root, "config.yaml")

    # Verification de l'existence du fichier
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"❌ Le fichier config.yaml est introuvable à : {yaml_path}")

    # Chargerment du fichier YAML
    with open(yaml_path, "r") as file:
        return yaml.safe_load(file)

# -----------------------------------------------
# Fonction pour charger tous les PDF d'un dossier
# -----------------------------------------------

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

# ----------------------------------------------------------------------------------
# Fonction pour creer des embeddings dynamiquement en fonction du modele selectionne
# ----------------------------------------------------------------------------------

def create_embeddings(model_name, embeddings_type, faiss_index_path):

    # On trouve le path du corpus et on charge les PDF
    directory_path = os.path.abspath("../corpus_v1.3/pdf")
    docs = load_all_pdfs_from_directory(directory_path)

    # On cree des documents a partir du contenu des PDF
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)

    # On selectionne le type d'embeddings voulu
    if embeddings_type == "OpenAIEmbeddings":
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    elif embeddings_type == "OllamaEmbeddings":
        embeddings = OllamaEmbeddings(model=model_name)
    else:
        raise ValueError(f"🚨 Type d'embedding inconnu : {embeddings_type}")

    # On cree et sauvegarde l'index FAISS
    # Cela peut prendre pas mal de temps
    # Pour accelerer, utiliser la librairie faiss-gpu pour une parallelisation GPU
    # Par exemple, on peut faire 'pip install faiss-gpu-cu12' pour faissgpu.cuda12
    # Les derniers drivers NVIDIA-proprietaire stables doivent etre installes.
    vector = FAISS.from_documents(documents, embeddings)
    faiss_index_path = os.path.abspath(faiss_index_path)
    vector.save_local(faiss_index_path)

    # Message de confirmation en cas de succes
    print(f"✅ Index FAISS créé et sauvegardé dans : {faiss_index_path}")

# --------------------------------------------------------------------------------
# Fonction principale de type 'if __name__ == "__main__":'
# ATTENTION 1 : CETTE FONCTION N'EST PAS EXECUTEE AUTOMATIQUEMENT EN CAS D'IMPORT
# Cela est du au fait que la generation FAISS est longue et intensive en calcul
# Il ne faut donc executer ce script utils.py que si on a change le corpus
# Si on a change le corpus, il mettra a jour les index FAISS pour le retriever
# ATTENTION 2 : CETTE FONCTION NE GENERE QUE LE FAISS DU MODELE PAR DEFAUT DU YAML
# Si le modele par defaut est llama3, ce script ne generera que le FAISS de llama3
# Il faut changer le modele par defaut dans le config.yaml pour switcher
# --------------------------------------------------------------------------------

if __name__ == "__main__":

    # Chargement de la configuration YAML
    config = load_config()
    # On selectionne le modele par defaut
    selected_model = config["llm"]["default_model"]
    # On charge la config specifique du modele par defaut
    model_config = config["llm"].get(selected_model)
    embeddings_type = model_config["embeddings"]
    faiss_index_path = model_config["faisspath"]
    # On remonte d'un cran dans l'arborescence pour le path de l'index faiss
    faiss_index_path = f"../{faiss_index_path}"

    # Message de confirmation du chargement du config.yaml
    print(f"✅ Fichier config.yaml chargé avec succès. Modèle sélectionné : {selected_model}")

    # On genere les embeddings
    print(f"🔍 Utilisation des embeddings {embeddings_type} pour {selected_model}...")
    create_embeddings(selected_model, embeddings_type, faiss_index_path)



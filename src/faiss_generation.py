# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import os
import yaml
import requests
import sys
from datetime import datetime

# Imports d'elements specifiques externes
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings    

# Import de variables (cle api)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from keys_file import OPENAI_API_KEY, HF_API_TOKEN, HF_API_URL_EMBEDDING

# -------------------------------------------------------------------------------------
# Classe HuggingFaceEmbeddings pour récupérer les embeddings via l'API de Hugging Face
# -------------------------------------------------------------------------------------

class HuggingFaceEmbeddings(Embeddings):
    """Classe pour récupérer les embeddings via l'API de Hugging Face."""

    def __init__(self, hf_api_url, hf_api_token, batch_size=32):
        self.hf_api_url = hf_api_url
        self.hf_api_token = hf_api_token
        self.batch_size = batch_size

    def _query_huggingface(self, texts):
        """Envoie un batch de textes à l'API Hugging Face et récupère les embeddings."""
        headers = {"Authorization": f"Bearer {self.hf_api_token}"}
        response = requests.post(self.hf_api_url, headers=headers, json={"inputs": texts})
        return response.json() if response.status_code == 200 else None

    def embed_documents(self, texts):
        """Embed une liste de documents en batch."""
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = self._query_huggingface(batch)
            if embeddings:
                all_embeddings.extend(embeddings)
        return all_embeddings

    def embed_query(self, text):
        """Embed une seule requête."""
        embedding = self._query_huggingface([text])
        return embedding[0] if embedding else None


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

def load_all_pdfs_from_directory(directory_path, log_files):
    pdf_documents = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_path = os.path.join(root, file)
                print(f"Ajout du fichier PDF : {file}")
                log_files.append(file)  # Ajout du chemin complet dans la liste de log
                loader = PyPDFLoader(file_path)
                pdf_documents.extend(loader.load())
    return pdf_documents

# ----------------------------------------------------------------------------------
# Fonction pour creer des embeddings dynamiquement en fonction du modele selectionne
# ----------------------------------------------------------------------------------

def create_embeddings(embeddings_type, faiss_index_path, directories):
    """
    Crée l'index FAISS à partir de PDF situés dans une liste de dossiers.
    
    :param model_name: Nom du modèle sélectionné
    :param embeddings_type: Type d'embedding à utiliser ("OpenAIEmbeddings" ou "HuggingFaceEmbeddings")
    :param faiss_index_path: Chemin où sauvegarder l'index FAISS (dossier ou fichier)
    :param directories: Liste de chemins absolus vers les dossiers contenant les PDF
    """

    # Liste pour conserver les chemins des fichiers PDF utilisés
    pdf_files_log = []

    # Charger les PDF depuis chacun des dossiers
    docs = []
    for directory_path in directories:
        abs_directory = os.path.abspath(directory_path)
        docs.extend(load_all_pdfs_from_directory(abs_directory, pdf_files_log))

    # Création des documents à partir du contenu des PDF
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)
    texts = [doc.page_content for doc in documents]

    # Sélection du type d'embedding voulu
    if embeddings_type == "OpenAIEmbeddings":
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vector = FAISS.from_documents(documents, embeddings)
    elif embeddings_type == "HuggingFaceEmbeddings":
        embedding_model = HuggingFaceEmbeddings(hf_api_url=HF_API_URL_EMBEDDING, hf_api_token=HF_API_TOKEN)
        document_embeddings = embedding_model.embed_documents(texts)
        text_embedding_pairs = list(zip(texts, document_embeddings))
        vector = FAISS.from_embeddings(text_embedding_pairs, embedding=embedding_model)
    else:
        raise ValueError(f"Type d'embedding inconnu : {embeddings_type}")

    # On crée et sauvegarde l'index FAISS
    faiss_index_path = os.path.abspath(faiss_index_path)
    vector.save_local(faiss_index_path)
    print(f"\n✅ Index FAISS créé et sauvegardé dans : {faiss_index_path}")

    # Création ou mise à jour du log dans le dossier contenant l'index FAISS
    formatted_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    log_filename = os.path.join(faiss_index_path, "log.txt")
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log_file.write("===================================================\n")
        log_file.write(f"\nCet index FAISS a été généré le {formatted_date}\n")
        log_file.write("Documents PDF utilisés :\n\n")
        for file in pdf_files_log:
            log_file.write(f"- {file}\n")
        log_file.write("\n===================================================\n\n")

# --------------------------------------------------------------------------------
# Fonction principale de type 'if __name__ == "__main__":'
# ATTENTION : CETTE FONCTION N'EST PAS EXECUTEE AUTOMATIQUEMENT EN CAS D'IMPORT
# Cela est du au fait que la generation FAISS est longue et intensive en calcul
# Il ne faut donc executer ce script utils.py que si on a change le corpus
# Si on a change le corpus, il mettra a jour les index FAISS pour le retriever
# --------------------------------------------------------------------------------

if __name__ == "__main__":

    # Message de début
    print("\n================= FAISS GENERATION SCRIPT =================\n")

    # Sélection du type de modèle
    i = 0
    while i not in (1, 2):
        i = int(input("Pour quel type de modèle voulez-vous générer l'index FAISS ? \nTapez 1 pour un modèle OpenAI.\nTapez 2 pour un modèle Llama.\n\nTapez votre choix : "))
    # Chargement de la configuration YAML
    config = load_config()

    # Message intermédiaire
    print("\n✅ Choix enregistré et config.yaml chargé avec succès.")

    # On charge la config specifique du modele choisi
    if i == 1 :
        selected_model = "gpt-4o"
    elif i == 2 : 
        selected_model = "llama3"
    model_config = config["llm"].get(selected_model)
    embeddings_type = model_config["embeddings"]
    faiss_index_path = model_config["faisspath"]

    # On remonte d'un cran dans l'arborescence pour le path de l'index faiss
    faiss_index_path = f"../{faiss_index_path}"
    # On définit les chemins d'accès aux dossiers contenant les PDF
    directories = ["../corpus/pdf_scrapes", "../corpus/pdf_ajoutes_manuellement"]

    # On genere les embeddings
    print(f"🔍 Utilisation des embeddings {embeddings_type} ... Veuillez patienter\n")
    create_embeddings(embeddings_type, faiss_index_path, directories)
    print(f"\n===========================================================\n")



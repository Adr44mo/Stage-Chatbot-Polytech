# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import os
import yaml
import requests
import sys

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
from src.keys_file import OPENAI_API_KEY, HF_API_TOKEN, HF_API_URL_EMBEDDING

# Vérification des valeurs
print("OPENAI_API_KEY:", OPENAI_API_KEY)
print("HF_API_TOKEN:", HF_API_TOKEN)
print("HF_API_URL_EMBEDDING:", HF_API_URL_EMBEDDING)



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
    directory_path = os.path.abspath("../corpus_v1.4/pdf")
    docs = load_all_pdfs_from_directory(directory_path)

    # On cree des documents a partir du contenu des PDF
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)
    texts = [doc.page_content for doc in documents]

    # On selectionne le type d'embeddings voulu
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

    # On cree et sauvegarde l'index FAISS
    # Cela peut prendre pas mal de temps
    # Pour accelerer, utiliser la librairie faiss-gpu pour une parallelisation GPU
    # Par exemple, on peut faire 'pip install faiss-gpu-cu12' pour faissgpu.cuda12
    # Les derniers drivers NVIDIA-proprietaire stables doivent etre installes.
    faiss_index_path = os.path.abspath(faiss_index_path)
    vector.save_local(faiss_index_path)

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
    selected_model = config["default_model_faiss"]
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



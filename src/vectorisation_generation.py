# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import os
import json
import yaml
import requests
import sys
import PyPDF2
import re
import shutil
from datetime import datetime

# Imports d'elements specifiques externes
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings    
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
from uuid import uuid4


# Import de variables (cle api)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.keys_file import OPENAI_API_KEY, HF_API_TOKEN, HF_API_URL_EMBEDDING

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

# ------------------------------------------------------------------------------------
# Fonction pour creer la vectorisation dynamiquement en fonction du modele selectionne
# ------------------------------------------------------------------------------------

def create_embeddings(model_name, vectorisation_path, pdf_directories):

    # GESTION FAISS CLASSIQUE POUR GPT-4O-MINI
    if model_name == "gpt-4o-mini" :

        print("\n⌛ Veuillez patienter, ChromaDB en cours de génération... \n")

        # Chargement des PDF
        pdf_files_log = []
        docs = []
        for directory_path in pdf_directories:
            abs_directory = os.path.abspath(directory_path)
            docs.extend(load_all_pdfs_from_directory(abs_directory, pdf_files_log))

        # Création des documents à partir du contenu des PDF
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        documents = text_splitter.split_documents(docs)

        # Selection des embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vector = FAISS.from_documents(documents, embeddings)

        # Enregistrement de la vectorisation
        vectorisation_path = os.path.abspath(vectorisation_path)
        vector.save_local(vectorisation_path)
        print(f"\n✅ Vectorisation FAISS créée et sauvegardée (avec log) dans : {vectorisation_path}")

        # Création ou mise à jour du log dans le dossier contenant la vectorisation
        formatted_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
        log_filename = os.path.join(vectorisation_path, "log.txt")
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write("===================================================\n")
            log_file.write(f"\nCette vectorisation a été générée le {formatted_date}\n")
            log_file.write("\nDocuments PDF utilisés :\n\n")
            for file in pdf_files_log:
                log_file.write(f"- {file}\n")
            log_file.write("\n===================================================\n\n")

    # GESTION FAISS AVEC EMBEDDINGS HUGGINGFACE POUR LLAMA3
    elif model_name == "llama3" :

        print("\n⌛ Veuillez patienter, ChromaDB en cours de génération... \n")

        # Chargement des PDF
        pdf_files_log = []
        docs = []
        for directory_path in pdf_directories:
            abs_directory = os.path.abspath(directory_path)
            docs.extend(load_all_pdfs_from_directory(abs_directory, pdf_files_log))

        # Création des documents à partir du contenu des PDF
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        documents = text_splitter.split_documents(docs)
        texts = [doc.page_content for doc in documents]

        # Selection des embeddings
        embedding_model = HuggingFaceEmbeddings(hf_api_url=HF_API_URL_EMBEDDING, hf_api_token=HF_API_TOKEN)
        document_embeddings = embedding_model.embed_documents(texts)
        text_embedding_pairs = list(zip(texts, document_embeddings))
        vector = FAISS.from_embeddings(text_embedding_pairs, embedding=embedding_model)

        # Enregistrement de la vectorisation
        vectorisation_path = os.path.abspath(vectorisation_path)
        vector.save_local(vectorisation_path)
        print(f"\n✅ Vectorisation FAISS créée et sauvegardée (avec log) dans : {vectorisation_path}")

        # Création ou mise à jour du log dans le dossier contenant la vectorisation
        formatted_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
        log_filename = os.path.join(vectorisation_path, "log.txt")
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write("===================================================\n")
            log_file.write(f"\nCette vectorisation a été générée le {formatted_date}\n")
            log_file.write("\nDocuments PDF utilisés :\n\n")
            for file in pdf_files_log:
                log_file.write(f"- {file}\n")
            log_file.write("\n===================================================\n\n")

    # GESTION CHROMADB POUR GPT-4O
    elif model_name == "gpt-4o":

        print("\n⌛ Veuillez patienter, ChromaDB en cours de génération... \n")
        SPECIALTIES = ["AGRAL (Agroalimentaire)", "EISE (Électronique - Informatique Parcours systèmes embarqués)", 
                       "EI2I (Électronique - Informatique Parcours informatique industrielle)", "GM (Génie Mécanique)", 
                       "MAIN (Mathématiques appliquées et informatique)", "MTX (Matériaux - Chimie)", 
                       "ROB (Robotique)", "ST (Sciences de la terre : aménagement, environnement, énergie)"]
        SPECIALITIES_short = {"AGRAL": "AGRAL (Agroalimentaire)", 
                              "EISE": "EISE (Électronique - Informatique Parcours systèmes embarqués)", 
                              "EI2I": "EI2I (Électronique - Informatique Parcours informatique industrielle)", 
                              "GM": "GM (Génie Mécanique)", 
                              "MAIN": "MAIN (Mathématiques appliquées et informatique)", 
                              "MTX": "MTX (Matériaux - Chimie)", 
                              "ROB": "ROB (Robotique)", 
                              "ST": "ST (Sciences de la terre : aménagement, environnement, énergie)"}
        try:
            documents = []
            json_files_log = []
            pdf_files_log = []
            # --- Traitement des fichiers JSON ---
            json_directory = os.path.abspath("../corpus/json_scrapes")
            json_corpus = []
            for root, _, files in os.walk(json_directory):
                for file in files:
                    if file.lower().endswith(".json"):
                        json_file_path = os.path.join(root, file)
                        json_corpus.append(json_file_path)
                        json_files_log.append(os.path.basename(json_file_path))
            for json_file in json_corpus:
                try:
                    loader = JSONLoader(
                        file_path=json_file,
                        jq_schema=".content",
                    )
                    unique_id = str(uuid4())
                    json_docs = loader.load()
                    
                    # Extraire et ajouter les métadonnées pour chaque document
                    for doc in json_docs:
                        statut = "publique" if "pub" in json_file.lower() or "public" in json_file.lower() else "privé"
                        speciality = None
                        for x in SPECIALTIES:
                            if x.lower() in json_file.lower():
                                speciality = x
                                break
                        # Lecture du contenu JSON pour extraire 'filierespecifique'
                        try:
                            with open(json_file, "r", encoding="utf-8") as f:
                                json_data = json.load(f)
                        except Exception as e:
                            print(f"❌ Erreur lors de l'ouverture de {json_file} : {e}")
                            json_data = {}
                        if speciality is None:
                            spec = json_data.get("filierespecifique", None)
                            if spec:
                                speciality = SPECIALITIES_short.get(spec, spec)
                            else:
                                speciality = "None"
                        metadata = {
                            "ID": unique_id,
                            "URL": json_data.get("url", ""),
                            "Status": statut,
                            "Speciality": speciality,
                            "Source": json_file,
                        }
                        doc.metadata.update(metadata)
                    documents.extend(json_docs)
                except Exception as e:
                    print("Erreur", f"Erreur lors du traitement de {json_file} : {str(e)}")
            
            # --- Traitement des fichiers PDF ---
            # Pour les PDF, on parcourt chacun des répertoires définis dans pdf_directories
            for directory in pdf_directories:
                abs_directory = os.path.abspath(directory)
                pdf_corpus = []
                for root, _, files in os.walk(abs_directory):
                    for file in files:
                        if file.lower().endswith(".pdf"):
                            pdf_file_path = os.path.join(root, file)
                            pdf_corpus.append(pdf_file_path)
                            pdf_files_log.append(os.path.basename(pdf_file_path))
                for pdf_file in pdf_corpus:
                    try:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        text = "".join(page.extract_text() for page in pdf_reader.pages)
                        if text:
                            text = re.sub(r"[ \t\r\f\v]*\n([ \t\r\f\v]*\n)+", "\n\n", text).strip()
                            text_splitter = RecursiveCharacterTextSplitter(
                                chunk_size=500,
                                chunk_overlap=50,
                                length_function=len,
                                is_separator_regex=False,
                            )
                            chunked_pdf = text_splitter.create_documents([text])
                            for chunk in chunked_pdf:
                                unique_id = str(uuid4())
                                statut = "publique" if "public" in pdf_file.lower() else "privé"
                                speciality = None
                                for x in SPECIALTIES:
                                    if x.lower() in pdf_file.lower():
                                        speciality = x
                                if speciality is None:
                                    speciality = "None"
                                metadata = {
                                    "ID": unique_id,
                                    "Source": pdf_file,
                                    "Status": statut,
                                    "Speciality": speciality,
                                }
                                chunk.metadata.update(metadata)
                            documents.extend(chunked_pdf)
                        else:
                            print("Attention", f"Aucun texte extrait de : {pdf_file}")
                    except Exception as e:
                        print("Erreur", f"Erreur lors du traitement de {pdf_file} : {str(e)}")
            
            # Création des embeddings et du vector store
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
            # On nettoie la DB pour régénerer la nouvelle
            if os.path.exists(vectorisation_path):
                shutil.rmtree(vectorisation_path)
            db = Chroma.from_documents(documents=documents, embedding=embeddings, collection_name="openai_chroma_db", persist_directory=vectorisation_path)
            
            print(f"✅ Vectorisation ChromaDB créée et sauvegardée (avec log) dans : {vectorisation_path}")
        
        except Exception as e:
            print("Erreur", f"Une erreur s'est produite : {str(e)}")

        #Enregistrement du log 
        formatted_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
        log_filename = os.path.join(vectorisation_path, "log.txt")
        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write("===================================================\n")
            log_file.write(f"\nCette vectorisation a été générée le {formatted_date}\n")
            log_file.write("\nFichiers JSON utilisés :\n\n")
            for file in json_files_log:
                log_file.write(f"- {file}\n")
            log_file.write("\nFichiers PDF utilisés :\n\n")
            for file in pdf_files_log:
                log_file.write(f"- {file}\n")
            log_file.write("\n===================================================\n\n")


# -------------------------------------------------------------------------------
# Fonction principale de type 'if __name__ == "__main__":'
# ATTENTION : CETTE FONCTION N'EST PAS EXECUTEE AUTOMATIQUEMENT EN CAS D'IMPORT
# Cela est du au fait que la generation vectoriellle est longue et intensive
# Il ne faut donc executer ce script utils.py que si on a change le corpus
# Si on a change le corpus, il mettra a jour les vectorisations pour le retriever
# -------------------------------------------------------------------------------

if __name__ == "__main__":

    # Message de début
    print("\n================= VECTORISATION GENERATION SCRIPT =================\n")

    # Sélection du type de modèle
    i = 0
    while i not in (1, 2, 3):
        i = int(input("Pour quel type de modèle voulez-vous générer la vectorisation ? \n\nTapez 1 pour GPT-4o-Mini.\nTapez 2 pour GPT-4o (avec metadata).\nTapez 3 pour LLaMA3. \n\nTapez votre choix : "))
    # Chargement de la configuration YAML
    config = load_config()

    # Message intermédiaire
    print("\n✅ Choix enregistré et config.yaml chargé avec succès.")

    # On charge la config specifique du modele choisi
    if i == 1 :
        selected_model = "gpt-4o-mini"
    elif i == 2 : 
        selected_model = "gpt-4o"
    elif i == 3 : 
        selected_model = "llama3"

    model_config = config["llm"].get(selected_model)
    model_name = model_config["model_name"]
    vectorisation_path = model_config["vectorisation_path"]

    # On remonte d'un cran dans l'arborescence pour le path de la vectorisation
    vectorisation_path = f"../{vectorisation_path}"
    # On définit les chemins d'accès aux dossiers contenant les PDF
    pdf_directories = ["../corpus/pdf_scrapes", "../corpus/pdf_ajoutes_manuellement"]

    # On genere la vectorisation
    create_embeddings(model_name, vectorisation_path, pdf_directories)
    print(f"\n===========================================================\n")



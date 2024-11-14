import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import configs

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

def create_embeddings():
    # Chemin absolu du dossier 'corpusv1/intranet' basé sur le répertoire courant
    directory_path = os.path.abspath("corpusv1/intranet")
    
    # Charger tous les fichiers PDF dans le dossier spécifié
    docs = load_all_pdfs_from_directory(directory_path)

    # Diviser les documents en petits segments
    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)

    # Créer les embeddings OpenAI pour chaque segment
    embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
    vector = FAISS.from_documents(documents, embeddings)

    # Sauvegarder l'index FAISS pour une utilisation future
    vector.save_local("faiss_index")
    print("Index FAISS créé et sauvegardé dans 'faiss_index'.")

# Appeler la fonction principale
create_embeddings()

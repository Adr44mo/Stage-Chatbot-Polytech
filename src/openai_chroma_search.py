# -----------------------
# Imports des utilitaires
# -----------------------

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
from typing import List, Optional
import json

# ---------------------------------------------------------------------
# Chargement de la base de données Chroma avec les embeddings d'OpenAI
# ---------------------------------------------------------------------
vectordb = Chroma(
    persist_directory="./Json1",    # Répertoire pour stocker les vecteurs et les métadonnées
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"), 
    collection_name="Json1"  
)

# --------------------------------------------------------------------------------------
# Définition du modèle de recherche avec Pydantic pour valider la structure des requêtes
# --------------------------------------------------------------------------------------
class Search(BaseModel):
    query: str = Field(..., description="Recherche par similarité appliquée à des documents d'informations sur l'école")
    specialty: Optional[str] = Field(None, description="Spécialité à rechercher (exemple: MAIN, INFO, MATH)")
    status: Optional[str] = Field(None, description="Statut du document, peut être 'publique' ou 'privé'")

# -------------------------------------------------------------------------------
# Fonction pour récupérer un document par son ID depuis la base de données Chroma
# -------------------------------------------------------------------------------
def get_document_by_id(collection, vector_id):
    results = collection.get(where={"ID": vector_id})
    if results and results["ids"]:
        return results 
    else:
        return None

# --------------------------------------------------------------------------------------------
# Fonction de recherche dans Chroma en fonction d'un critère spécifique (spécialité, statut)
# --------------------------------------------------------------------------------------------
def retrieval_single_field(search: Search, field: str, value) -> List[str]:
    _filter = {}
    if field == "Specialty":
        _filter["Specialty"] = search.specialty
    if field == "Status":
        _filter["Status"] = search.status
    
    results = vectordb.similarity_search(search.query, filter=_filter)
    return [doc.metadata.get("ID", 'None') for doc in results]

# --------------------------------------------------------------------------------------------
# Recherche des documents dans Chroma en appliquant des filtres sur la spécialité et le statut
# --------------------------------------------------------------------------------------------
def retrieval(search: Search) -> List[Document]:
    all_ids_set = set() 

    if search.specialty:
        all_ids_set.update(retrieval_single_field(search, "Specialty", search.specialty))
    if search.status:
        all_ids_set.update(retrieval_single_field(search, "Status", search.status))

    return list(all_ids_set)

# -------------------------------------------------------------------------------------------------
# Fonction de détection des filtres dans la question de l'utilisateur (extraction des spécialités)
# -------------------------------------------------------------------------------------------------
def filter_detection(question) -> dict:
    SPECIALTIES = [
        "AGRAL (Agroalimentaire)", 
        "EISE (Électronique - Informatique Parcours systèmes embarqués)",
        "EI2I (Électronique - Informatique Parcours informatique industrielle)", 
        "GM (Génie Mécanique)",
        "MAIN (Mathématiques appliquées et informatique)", 
        "MTX (Matériaux - Chimie)", 
        "ROB (Robotique)",
        "ST (Sciences de la terre : aménagement, environnement, énergie)"
    ]
    
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0) 
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Tu es un assistant chargé d'extraire des filtres de métadonnées à partir d'une question. Voici les filtres qui nous intéressent : specialty. Plusieurs informations peuvent être ajoutées dans le même filtre. Voici une liste des spécialités reconnues : {SPECIALTIES}."),
        ("human", "Voici la question de l'utilisateur : {question}. Retourne les informations au format JSON avec 'None' si rien ne correspond.")
    ])

    # Chaîne de traitement pour passer la question au modèle
    FilterChain = (prompt | llm | RunnablePassthrough())
    response = FilterChain.invoke({"question": question, "SPECIALTIES":SPECIALTIES})
    response = str(response.content)
    dict_answer = json.loads(response)
    return dict_answer
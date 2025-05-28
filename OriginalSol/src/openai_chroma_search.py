# -----------------------
# Imports des utilitaires
# -----------------------

from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from typing import List
import json

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
def retrieval_single_field(query: str, filters: dict, vectordb: Chroma):    
    docs = vectordb.similarity_search(query, k=5, filter=filters)
    return [doc.metadata.get("ID", 'None') for doc in docs]

# --------------------------------------------------------------------------------------------
# Recherche des documents dans Chroma en appliquant des filtres sur la spécialité et le statut
# --------------------------------------------------------------------------------------------
def retrieval(query: str, filters: list, vectordb: Chroma) -> List[Document]:
    all_ids_set = set()

    # Si des filtres de spécialité sont fournis
    if filters and filters != ['None']:
        for _filter in filters:
            all_ids_set.update(retrieval_single_field(query, {"Speciality": _filter}, vectordb))
    else:
        all_ids_set.update(retrieval_single_field(query, {"Status": "privé"}, vectordb))

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
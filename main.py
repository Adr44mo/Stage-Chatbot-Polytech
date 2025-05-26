# -----------------------
# Imports des utilitaires
# -----------------------

print("\n================= LANCEMENT DE POLYCHAT =================\n")

import os

# Ensure correct port binding for Render
os.environ["STREAMLIT_SERVER_PORT"] = os.environ.get("PORT", "8501")
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

# Imports de librairies
import yaml
import os
import json
import streamlit as st
import requests

# Imports d'elements specifiques externes
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS, Chroma
from openai import OpenAI

# Affichage d'un message de succès d'import des librairies
print("\n✅ Librairies externes correctement chargées !")

# Imports de fonctions depuis llm.py
from src.llm import query_rag
from src.vectorisation_generation import HuggingFaceEmbeddings
from src.openai_chroma_search import get_document_by_id, filter_detection, retrieval

# Imports de fonctions depuis filters.py
from src.filters import handle_if_uninformative

# Import de variables (url, cle api, token)
from src.keys_file import OPENAI_API_KEY, HF_API_TOKEN, HF_API_URL, HF_API_URL_EMBEDDING
print("✅ Fonctions et variables internes correctement chargées !")

# -------------------------------------------------------
# Classe OpenAIEndpointLLM pour interroger un endpoint HF
# Cet endpoint huggingface est interroge via l'api OpenAI
# -------------------------------------------------------

class OpenAIEndpointLLM:

    # Fonction qui initialise l'instance de l'API Hugging Face sous une API OpenAI-compatible
    def __init__(self, model, temperature, base_url, api_key, max_tokens=150):
        self.model = model
        self.temperature = temperature
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    # Fonction qui envoie une requete au modele avec les messages fournis
    def invoke(self, inputs):
        prompt_input = inputs.get("input", "")
        if isinstance(prompt_input, list):
            messages = prompt_input
        else:
            messages = [{"role": "user", "content": str(prompt_input)}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=None,
            seed=None,
            stop=None,
            frequency_penalty=None,
            presence_penalty=None,
            stream=False
        )
        answer = response.choices[0].message.content
        return answer

    # Fonction qui appelle l'instance de la classe directement avec un prompt
    def __call__(self, prompt):
        if isinstance(prompt, list):
            return self.invoke({"input": prompt})
        return self.invoke({"input": str(prompt)})

# -------------------------------------------------
# Chargement de la configuration depuis config.yaml
# -------------------------------------------------

# Fonction de chargement de la config
def load_config(yaml_path="config.yaml"):
    with open(yaml_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

# On charge activement cette config
config = load_config()
print("✅ Configuration YAML correctement chargée !")
ALL_MODELS = ["gpt-4o-mini", "gpt-4o", "llama3"]

# ------------------------------------------------------------
# Fonctions de gestion de l’historique (sauvegarde/chargement)
# Cette logique vaut pour un deploiement web-app
# Elle doit etre adaptee si l'on veut tourner en local
# ------------------------------------------------------------

# Repertoire de stockage des fichiers d'historique
BASE_HISTORY_DIR = "/var/data"

# Fonction pour recuperer le user_id
def get_user_id_from_url() -> str:
    params = st.query_params
    user_id_list = params.get("user_id", [])
    return user_id_list[0] if user_id_list else ""

# Fonction pour ecuperer le fichier d'historique correspondant a l'utilisateur
def get_user_history_file(user_id):
    user_dir = os.path.join(BASE_HISTORY_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "history.json")

# Fonction pour charger ce fichier d'historique
def load_history(user_id):
    history_file = get_user_history_file(user_id)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Erreur lors du chargement de l'historique :", e)
    return []

# Fonction pour enregistrer un historique
def save_history(user_id, history):
    history_file = get_user_history_file(user_id)
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Erreur lors de la sauvegarde de l'historique :", e)

# -------------------------------------
# Initialisation du LLM et du Retriever
# -------------------------------------

def init_llm_and_retriever(model_choice):

    # Recuperation des parametres du modele voulu dans le config.yaml
    llm_config = config["llm"].get(model_choice)
    if not llm_config:
        raise ValueError(f"Modèle '{model_choice}' non reconnu dans config.yaml.")
    embedding_type = llm_config["embeddings"]
    vectorisation_path = llm_config["vectorisation_path"]

    # Definition des embeddings
    if embedding_type == "OpenAIEmbeddings": # pour gpt
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    elif embedding_type == "OpenAIEmbeddingsMetadata":
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key =OPENAI_API_KEY)
    elif embedding_type == "HuggingFaceEmbeddings": # pour llama
        embeddings = HuggingFaceEmbeddings(hf_api_url=HF_API_URL_EMBEDDING, hf_api_token=HF_API_TOKEN)
    else:
        raise ValueError("Type d'embeddings inconnu ou non géré.")
    
    # Chargement de l'index FAISS / Chroma pour gpt-4o
    if model_choice == "gpt-4o":
        vector = Chroma(persist_directory=vectorisation_path, embedding_function=embeddings, collection_name="openai_chroma_db")
    else:
        vector = FAISS.load_local(vectorisation_path, embeddings, allow_dangerous_deserialization=True)
    
    retriever = vector.as_retriever()

    # GPT : on definit la variable llm
    if model_choice in ["gpt-4o", "gpt-4o-mini"]:
        llm = ChatOpenAI(
            model_name=llm_config["model_name"],
            temperature=llm_config["temperature"],
            openai_api_key=OPENAI_API_KEY
        )

    # Llama : on definit la variable llm
    elif model_choice == "llama3":
        hf_endpoint_url = HF_API_URL
        hf_api_token = HF_API_TOKEN
        llm = OpenAIEndpointLLM(
            model="hermes-3-1-8b-gguf-abu",
            temperature=llm_config["temperature"],
            base_url=hf_endpoint_url,
            api_key=hf_api_token,
            max_tokens=1200
        )

    # On retourne les variables bien initialisees
    return vector, llm, retriever

# ----------------------------------------------------------------------------------
# Interface Streamlit
# Cette fonction est mise a jour dynamiquement a chaque fois que model_choice change
# ----------------------------------------------------------------------------------

def show_ui():

    # On force la customisation de l'interface graphique de streamlit
    st.markdown(
        """
        <style>
        [data-testid="stChatMessageAvatarUser"][aria-label="assistant"] svg { background-color: #FFFFFF !important; }
        [data-testid="stChatMessageAvatarUser"][aria-label="user"] { background-color: #429DDA !important; }
        [data-testid="stAppHeader"] { display: block !important; }
        [data-testid="stHeader"] { height:40px!important; border-bottom: 2px solid !important; border-image: linear-gradient(90deg, rgb(66, 157, 218), rgb(188, 236, 255)) 1 !important; }
        [data-testid="stDecoration"] { background-image: linear-gradient(90deg, rgb(66, 157, 218), rgb(188, 236, 255))!important; }
        [data-testid="stChatMessageAvatarUser"] { background: #429DDA !important; }
        [data-testid="stMainBlockContainer"] { padding-top:16px!important; overflow: visible !important; }
        [data-testid="stBottomBlockContainer"] { padding-bottom:30px!important; }
        [data-testid="stBottom"] { height:70px!important; }
        [data-testid="stHeaderActionElements"] { display:none!important; }
        [data-testid="stSelectbox"], [data-testid="stSelectbox"] * { cursor: pointer !important; }
        [data-testid="stSelectbox"] { position: sticky !important; top:0!important; z-index: 1000; background: #ffffff; }
        [data-testid="stSidebar"] { height: 90px !important; max-width:336px!important; width:100%!important; overflow:hidden; }
        [data-testid="stSidebarContent"] { padding-top: 10px !important; }
        [data-testid="stSidebarCollapsedControl"] { margin-top: -19px!important; }
        [data-testid="stSidebarHeader"] { display: none!important; }
        [data-testid="stSidebarUserContent"] { padding-bottom:0px!important; }
        [data-testid="stSidebarCollapsedControl"]::after { content: "Changer de LLM"; margin-left: 15px; font-size: 14px; color: inherit; }
    </style>
        """,
        unsafe_allow_html=True
    )

    # Autres parametrages pour l'interface graphique
    st.header("PolyChat", divider=False)
    with st.sidebar:
        model_choice = st.selectbox("Choisissez un modèle :", ALL_MODELS, index=0)
    st.info(f"Modèle actuellement utilisé : {model_choice}")
    st.write("Le ChatBot de Polytech-Sorbonne qui répondra à toutes vos questions !")

    # On initialise llm et retriever
    try:
        vector, llm, retriever = init_llm_and_retriever(model_choice)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # On obtient le user id
    user_id = get_user_id_from_url()
    if not user_id:
        st.error("Aucun user_id fourni dans l’URL (ex. ?user_id=ABC123).")
        st.stop()

    # On recupere un historique
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = load_history(user_id)

    # --------------ANCIENNE METHODE 
    # # Si cet historique et vierge, on envoie le premier message par défaut
    # if len(st.session_state["chat_history"]) == 0:
    #     init_user_msg = (
    #         "Présente-toi en tant que chatbot représentant Polytech-Sorbonne. "
    #         "Présente l'école en quelques mots et explique l'objet de ton appel."
    #     )
    #     # if model_choice == "llama3" :
    #     #     response = query_norag(llm, retriever, init_user_msg, [])
    #     # else :
    #     response = query_rag(llm, retriever, init_user_msg, [])
    #     st.session_state["chat_history"].extend([
    #         {"role": "user", "content": init_user_msg},
    #         {"role": "assistant", "content": response if isinstance(response, str) else response["answer"]},
    #     ])
    #     save_history(user_id, st.session_state["chat_history"])
    # --------------

    # Si l'historique est vide, afficher un message d'introduction statique
    if len(st.session_state["chat_history"]) == 0:
        st.info(
            "👋 Bonjour, je suis le chatbot représentant Polytech-Sorbonne. "
            "Posez-moi vos questions sur l'école, je vous répondrai avec plaisir !"
        )

    # On affiche l'historique precedent
    for message in st.session_state["chat_history"]:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "assistant":
            with st.chat_message("assistant", avatar="web/assets/logopolytech.svg"):
                st.markdown(content)
        else:
            with st.chat_message("user"):
                st.markdown(content)

    # A chaque nouveau message envoye par l'utilisateur 
    user_input = st.chat_input("Posez votre question ici...")
    if user_input:

        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("Patience..."):
            try:
                # On filtre le message de l'utilisateur pour éviter les appels à l'API inutiles 
                filtered_response = handle_if_uninformative(user_input)
                if filtered_response:
                    response = filtered_response
                
                else:
                    response = query_rag(llm, retriever, user_input, st.session_state["chat_history"])

            except requests.exceptions.ConnectionError:
                st.error(
                    "Impossible de se connecter au serveur d'inference. "
                    "Verifiez que votre endpoint est bien lance, accessible et que votre token est valide."
                )
                st.stop()

            # On verifie que la reponse est au bon format
            if isinstance(response, str):
                bot_answer = response
            elif isinstance(response, dict) and "answer" in response:
                bot_answer = response["answer"]
            elif hasattr(response, "content"):
                bot_answer = response.content
            else:
                bot_answer = str(response)

            # Vérification des liens pour cette question (si appel à l'API)
            if not filtered_response:

                if model_choice == "gpt-4o":
                    dict_answer = filter_detection(user_input)
                    spec = dict_answer.get('specialty', [])
                    if spec == "None":
                        spec = []
                    retrieved_documents = retrieval(query=user_input, filters=spec, vectordb=vector)

                    document_urls = set()  # Utilisation d'un set pour éviter les doublons
                    for doc_id in retrieved_documents:
                        doc = get_document_by_id(vector, doc_id)
                        if doc:  # Si le document existe
                            url = doc.get('metadatas', [{}])[0].get('URL', None)
                            if url:
                                document_urls.add(url)

                    if document_urls:
                        urls_str = ", ".join([f"{url}" for url in document_urls])
                        bot_answer += "\n\nSource : " + urls_str

            # On met a jour l'historique pour y ajouter la reponse
            with st.chat_message("assistant", avatar="web/assets/logopolytech.svg"):
                st.markdown(bot_answer)
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_answer})
            save_history(user_id, st.session_state["chat_history"])

#--------------------------------------------------------------------
# Fonction principale : on fait tourner show_ui() 
# Cela ne pose pas probleme car show_ui() se met a jour dynamiquement
#--------------------------------------------------------------------

print("✅ Fonction principale et interface streamlit correctement définies !")
print("⚡ Polychat est désormais actif ! \n")
print("\n=========================================================")

if __name__ == "__main__":
    show_ui()
import os
import json
import streamlit as st

import configs
from src.llm import query
from src.utils import create_embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS

embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
vector = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = vector.as_retriever()
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5, openai_api_key=configs.OPENAI_API_KEY)

BASE_HISTORY_DIR = "/var/data"

def get_user_id_from_url() -> str:
    params = st.query_params
    user_id_list = params.get("user_id", [])
    return user_id_list[0] if user_id_list else ""

def get_user_history_file(user_id):
    user_dir = os.path.join(BASE_HISTORY_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "history.json")

def load_history(user_id):
    history_file = get_user_history_file(user_id)
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_history(user_id, history):
    history_file = get_user_history_file(user_id)
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass

def show_ui():
    st.title("PolyChat")
    st.write("Le ChatBot de Polytech-Sorbonne qui répondra à toutes vos questions !")
    st.markdown(
        """
        <style>
        [data-testid="stChatMessageAvatar"][aria-label="assistant"] svg {
            background-color: #FFFFFF !important;
        }
        [data-testid="stChatMessageAvatar"][aria-label="user"] svg {
            background-color: #ADD8E6 !important;
        }
         [data-testid="stAppHeader"] {
        display: none !important;
    }   
    [data-testid="stHeader"] { height:30px!important; }
       
     
     [data-testid="stDecoration"] {
                background-image: linear-gradient(90deg, rgb(188 236 255), rgb(66 157 218))!important;}

         [data-testid="stMainBlockContainer"] {
                padding-top:16px!important;}        
                
                

 [data-testid="stBottomBlockContainer"] {
        padding-bottom:30px!important;
    }
    [data-testid="stBottom"] {
        height:70px!important;
    }
        </style>
        """,
        unsafe_allow_html=True
    )
    user_id = get_user_id_from_url()
    if not user_id:
        st.error("Aucun user_id fourni dans l’URL (ex. ?user_id=ABC123).")
        st.stop()
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = load_history(user_id)
    if len(st.session_state["chat_history"]) == 0:
        init_user_msg = "Présente toi et présente les articles qui pourraient intéresser le client"
        response = query(llm, retriever, "Présente toi, dis quel est l'objet de ton appel et présente les articles qui pourraient intéresser le client", [])
        st.session_state["chat_history"].extend([
            {"role": "user", "content": init_user_msg},
            {"role": "assistant", "content": response["answer"]},
        ])
        save_history(user_id, st.session_state["chat_history"])
    for message in st.session_state["chat_history"]:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "assistant":
            with st.chat_message("assistant", avatar="logopolytech.svg"):
                st.markdown(content)
        else:
            with st.chat_message("user", avatar="user.svg"):
                st.markdown(content)
    user_input = st.chat_input("Posez votre question ici...")
    if user_input:
        with st.spinner("Patience..."):
            with st.chat_message("user", avatar="user.svg"):
                st.markdown(user_input)
            response = query(llm, retriever, user_input, st.session_state["chat_history"])
            bot_answer = response["answer"]
            with st.chat_message("assistant", avatar="logopolytech.svg"):
                st.markdown(bot_answer)
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_answer})
            save_history(user_id, st.session_state["chat_history"])

if __name__ == "__main__":
    show_ui()

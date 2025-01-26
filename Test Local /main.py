import yaml
import os
import json
import streamlit as st
import configs 

from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage

from src.llm import query
from src.utils import create_embeddings

# 🔹 Charger la configuration YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# 🔹 CHOISIS LE MODÈLE ICI 🔥 (MODIFIER CETTE VARIABLE)
MODEL_CHOICE = "gpt-4o-mini"  # Peut être "gpt-4o", "gpt-4o-mini" ou "llama3"

# 🔹 Récupérer la configuration du modèle choisi
llm_config = config["llm"].get(MODEL_CHOICE)
if not llm_config:
    raise ValueError(f"🚨 Modèle '{MODEL_CHOICE}' non reconnu ! Vérifiez `config.yaml`.")

# 🔹 Sélection des embeddings en fonction du modèle
if llm_config["embeddings"] == "OpenAIEmbeddings":
    embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
elif llm_config["embeddings"] == "OllamaEmbeddings":
    from langchain_community.embeddings import OllamaEmbeddings
    embeddings = OllamaEmbeddings(model_name="llama3")

# 🔹 Charger FAISS avec les embeddings sélectionnés
vector = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = vector.as_retriever()

# 🔹 Initialisation du LLM
if MODEL_CHOICE in ["gpt-4o", "gpt-4o-mini"]:
    llm = ChatOpenAI(
        model_name=llm_config["model_name"],
        temperature=llm_config["temperature"],
        openai_api_key=configs.OPENAI_API_KEY
    )
elif MODEL_CHOICE == "llama3":
    from langchain_community.chat_models import Ollama
    llm = Ollama(
        model="llama3",
        temperature=llm_config["temperature"]
    )

def show_ui():
    st.title("Polychat")  
    st.info(f"💡 Modèle utilisé : `{MODEL_CHOICE}`")

    if "messages" not in st.session_state:
        st.session_state.chat_history = []
        response = query(llm, retriever, "Introduce yourself", st.session_state.chat_history)
        st.session_state.messages = [{"role": "assistant", "content": response["answer"]}]
        st.session_state.chat_history.extend(
            [
                HumanMessage(content="Introduce yourself"),
                AIMessage(content=response["answer"]),
            ]
        )
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Entrez votre question :) "):
        with st.spinner("Patience ..."):     
            response = query(llm, retriever, prompt, st.session_state.chat_history)
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                st.markdown(response["answer"])    

            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            st.session_state.chat_history.extend(
                [
                    HumanMessage(content=prompt),
                    AIMessage(content=response["answer"]),
                ]
            )

if __name__ == "__main__":
    show_ui()

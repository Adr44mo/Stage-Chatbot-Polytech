# main.py
print("\n================= LANCEMENT DE POLYCHAT =================\n")

import os
import chromadb
from pathlib import Path
import sys
import streamlit as st
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

# Configuration
from src.keys_file import (
    OPENAI_API_KEY,
    HF_API_TOKEN,
    HF_API_URL,
    HF_API_URL_EMBEDDING,
)
from src.llmm import initialize_the_rag_chain
from src.filters import handle_if_uninformative

# --------------------------
# Streamlit UI
# --------------------------


def format_sources(context):
    """Extract and format sources from context documents."""
    sources = set()

    for doc in context:
        metadata = getattr(doc, "metadata", {})

        url = metadata.get("url", "").strip()
        source = metadata.get("source", "").strip()

        if url:
            sources.add(url)
        elif source:
            sources.add(source)

    return "\n".join(f"• {src}\n" for src in sources) if sources else "Aucune source identifiée"



def show_ui():
    # UI Styling
    st.markdown( """
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

    st.header("PolyChat", divider=False)
    st.write("ChatBot de Polytech-Sorbonne - Réponses vérifiées avec sources")

    # Initialize components
    rag_chain = initialize_the_rag_chain()

    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display history
    for msg in st.session_state.chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role, avatar="web/assets/logopolytech.svg" if role == "assistant" else None):
            st.markdown(msg["content"])
            if role == "assistant" and "sources" in msg:
                st.caption("Sources :")
                st.markdown(f"<small>{msg['sources']}</small>", unsafe_allow_html=True)

    # Handle input
    if prompt := st.chat_input("Posez votre question ici..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.spinner("Recherche dans les documents..."):

            # On filtre le message de l'utilisateur pour éviter les appels à l'API inutiles 
                filtered_response = handle_if_uninformative(prompt)
                if filtered_response:
                    response = filtered_response

                else:
                    response = rag_chain.invoke({
                        "input": prompt,
                        "chat_history": [msg for msg in st.session_state.chat_history if msg["role"] == "assistant"]
                    })

                    answer = response["answer"]
                    sources = format_sources(response["context"])

        # Display response with sources
        with st.chat_message("assistant", avatar="web/assets/logopolytech.svg"):
            if filtered_response:
                answer = filtered_response
                sources = "Aucune source identifiée"
                st.markdown(answer)
            else:
                st.markdown(answer)
                st.divider()
                st.caption("**Sources utilisées :**")
                st.markdown(f"<small>{sources}</small>", unsafe_allow_html=True)

        # Update history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

if __name__ == "__main__":
    show_ui()
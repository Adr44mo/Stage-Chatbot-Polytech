from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage
import os
import json
import streamlit as st

import configs
from src.llm import query
from src.utils import create_embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores import FAISS




# from src.utils import create_embeddings

import streamlit as st
import configs


#create_embeddings()

embeddings = OpenAIEmbeddings(openai_api_key=configs.OPENAI_API_KEY)
vector = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
retriever = vector.as_retriever()
llm = ChatOpenAI(model_name="gpt-4o", temperature=0.5, openai_api_key=configs.OPENAI_API_KEY)
#llm = Ollama(model="llama2")


def show_ui():
    st.title("Polychat")  
    
    if "messages" not in st.session_state:
        st.session_state.chat_history = []
        response = query(llm,retriever,"Introduce yourself", st.session_state.chat_history)
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
            response = query(llm,retriever,prompt,st.session_state.chat_history)
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

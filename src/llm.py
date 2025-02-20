# -----------------------
# Imports des utilitaires
# -----------------------

# Imports d'elements specifiques externes
from langchain.chains import create_history_aware_retriever
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Imports de fonctions depuis prompts.py
from src.prompts import qa_prompt, contextualize_q_prompt

# -----------------------------------------------------------------
# Fonction definissant une query avec un retriever actif (pour RAG)
# -----------------------------------------------------------------

def query_rag(llm,retriever,question,chat_history):
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain.invoke({"input": question, "chat_history": chat_history})

# -------------------------------------------------------------------------------------------
# Fonction definissant une query query sans retriever actif (pour systeme simpliste sans RAG)
# Elle n'est pas utilisée mais peut servir à des fins de test quand le retriever buggue.
# -------------------------------------------------------------------------------------------

def query_norag(llm, retriever, question, chat_history):
    #retriever non-utilise ici
    final_messages = qa_prompt.format_messages(chat_history=chat_history, input=question, context="")
    response = llm(final_messages)
    return response
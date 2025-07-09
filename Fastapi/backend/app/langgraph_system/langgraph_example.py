# ==================================================================
# Test d'utilisation de LangGraph pour implémenter un système de RAG
# ==================================================================

# Importation des clés API
from keys_file import OPENAI_API_KEY

# Imports des librairies nécessaires
from typing import TypedDict, List, Optional, Union
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage
from pathlib import Path

# Répertoire de persistance pour la base de données vectorielle Chroma
persist_directory = Path(__file__).parent.parent.parent / "vectorisation" / "src" / "db"  
print(f"[INFO] Using persist directory: {persist_directory}")  

# Initialisation des embeddings OpenAI
embeddings = OpenAIEmbeddings()
db = Chroma(
    persist_directory=str(persist_directory),
    embedding_function=embeddings,
    collection_name="langchain"
)

# Initialisation du modèle de langage
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# ===================================
# Définition de l'état du graphe RAG
# ===================================

class RAGState(TypedDict):
    input_question: str
    chat_history: List[Union[HumanMessage, AIMessage]]  # liste des messages
    specialized_question: Optional[str]
    docs: Optional[List[str]]
    answer: Optional[str]

# =================================================
# Fonctions de traitement pour le graphe d'état RAG
# =================================================

def contextualize(state: RAGState) -> RAGState:
    """
    Contextualise la question de l'utilisateur en tenant compte de l'historique de la conversation.
    Reformule la question pour une recherche plus précise.
    """
    history_text = "\n".join(f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}" for msg in state["chat_history"])
    prompt = f"Historique:\n{history_text}\nReformule et spécialise la question suivante pour une recherche précise:\n{state['input_question']}"
    specialized_question = llm([HumanMessage(content=prompt)])
    return {"specialized_question": specialized_question.content}

def intent(state: RAGState) -> RAGState:
    """
    Détermine si la question de l'utilisateur nécessite une étape de récupération de documents (RAG) ou si elle peut être répondue directement.
    Analyse l'intention derrière la question.
    """
    prompt = (
        "You are an assistant working for a university chatbot. Your task is to determine whether the user's message requires a document retrieval step (RAG) to be answered, or if it can be answered directly by the AI.\n"
        "\n"
        "Consider: the conversation history and the current user question.\n"
        "\n"
        "Rules:\n"
        "- If the question asks for specific, factual information, documents, regulations, programs, lists, or details from university resources, respond: RAG_NEEDED.\n"
        "- If the question is general, conversational, or can be answered without documents (e.g., greetings, how the chatbot works, simple explanations), respond: DIRECT_ANSWER.\n"
        "\n"
        "Reply only with RAG_NEEDED or DIRECT_ANSWER.\n"
        "\n"
        f"History:\n{''.join([f'User: {msg.content}\n' if isinstance(msg, HumanMessage) else f'AI: {msg.content}\n' for msg in state['chat_history']])}"
        f"Question:\n{state['input_question']}"
    )
    result = llm([HumanMessage(content=prompt)])
    return {"intent": result.content.strip()}

def retrieval(state: RAGState) -> RAGState:
    """
    Récupère les documents pertinents en fonction de la question spécialisée.
    Utilise la base de données vectorielle pour trouver les documents les plus pertinents.
    """
    docs = db.similarity_search(state["specialized_question"], k=5)
    return {"docs": [doc.page_content for doc in docs]}

def generation(state: RAGState) -> RAGState:
    """
    Génère la réponse finale en utilisant l'historique de conversation et les documents récupérés.
    Si des documents sont présents, les intègre dans la réponse.
    """
    history_text = "\n".join(
        f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}"
        for msg in state["chat_history"]
    )
    # Si des documents sont présents, on fait du RAG, sinon réponse directe
    if state.get("docs"):
        context = "\n".join(state["docs"])
        prompt = f"Historique:\n{history_text}\nContexte:\n{context}\nQuestion:\n{state['input_question']}"
    else:
        prompt = f"Historique:\n{history_text}\nQuestion:\n{state['input_question']}"
    answer = llm([HumanMessage(content=prompt)])
    return {"answer": answer.content}

# =======================================
# Structure du graphe d'état pour le RAG
# =======================================

builder = StateGraph(RAGState)
builder.add_node("contextualize", contextualize)
builder.add_node("intent", intent)
builder.add_node("retrieval", retrieval)
builder.add_node("generation", generation)

builder.set_entry_point("contextualize")
builder.add_edge("contextualize", "intent")

builder.add_conditional_edges(
    "intent",
    lambda state: state["intent"],
    {
        "RAG_NEEDED": "retrieval",
        "DIRECT_ANSWER": "generation"
    }
)

builder.add_edge("retrieval", "generation")
builder.set_finish_point("generation")

rag_graph = builder.compile()

# ======================================
# Affichage du graphe pour visualisation
# ======================================

output_path = Path(__file__).parent / "rag_graph_example.png"
with open(output_path, "wb") as f:
    f.write(rag_graph.get_graph().draw_mermaid_png())

# ======================
# Test de la chaîne RAG
# ======================

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, AIMessage

    chat_history = []

    questions = [
        "Qu'est-ce que MAIN ?",
        "Quels sont les cours associés ?",
        "Bonjour, que peux-tu faire ?",
        "Peut-on faire de l'alternance?"
    ]
    for i, question in enumerate(questions, 1):
        output = rag_graph.invoke({"input_question": question, "chat_history": chat_history})
        print(f"Q{i}: {question}")
        print(f"A{i}: {output['answer']}")
        if output.get("docs"):
            print(f"[LOG] RAG utilisé pour Q{i}")
        else:
            print(f"[LOG] Réponse directe (pas de RAG) pour Q{i}")
        print("-" * 40)
        chat_history.extend([HumanMessage(content=question), AIMessage(content=output["answer"])])

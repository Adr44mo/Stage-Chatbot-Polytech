from langgraph.graph import StateGraph
from typing import TypedDict, List, Optional, Union

from langchain_openai import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage

from pathlib import Path
persist_directory = Path(__file__).parent.parent.parent / "vectorisation" / "src" / "db"  # Define the directory where the Chroma vector database will be persisted
print(f"[INFO] Using persist directory: {persist_directory}")  # Print the persist directory being used

embeddings = OpenAIEmbeddings()
db = Chroma(
    persist_directory=str(persist_directory),
    embedding_function=embeddings,
    collection_name="langchain"
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

class RAGState(TypedDict):
    input_question: str
    chat_history: List[Union[HumanMessage, AIMessage]]  # liste des messages
    specialized_question: Optional[str]
    docs: Optional[List[str]]
    answer: Optional[str]

def contextualize(state: RAGState) -> RAGState:
    # Construire un prompt en tenant compte de l'historique
    history_text = "\n".join(f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}" for msg in state["chat_history"])
    prompt = f"Historique:\n{history_text}\nReformule et spécialise la question suivante pour une recherche précise:\n{state['input_question']}"
    specialized_question = llm([HumanMessage(content=prompt)])
    return {"specialized_question": specialized_question.content}

def retrieval(state: RAGState) -> RAGState:
    docs = db.similarity_search(state["specialized_question"], k=5)
    return {"docs": [doc.page_content for doc in docs]}

def generation(state: RAGState) -> RAGState:
    context = "\n".join(state["docs"])
    history_text = "\n".join(f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"AI: {msg.content}" for msg in state["chat_history"])
    prompt = f"Historique:\n{history_text}\nContexte:\n{context}\nQuestion:\n{state['input_question']}"
    answer = llm([HumanMessage(content=prompt)])
    return {"answer": answer.content}

builder = StateGraph(RAGState)
builder.add_node("contextualize", contextualize)
builder.add_node("retrieval", retrieval)
builder.add_node("generation", generation)

builder.set_entry_point("contextualize")
builder.add_edge("contextualize", "retrieval")
builder.add_edge("retrieval", "generation")
builder.set_finish_point("generation")

rag_graph = builder.compile()

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, AIMessage

    chat_history = []

    # 1ère question
    question1 = "Qu'est-ce que MAIN ?"
    output1 = rag_graph.invoke({"input_question": question1, "chat_history": chat_history})
    print("Q1:", question1)
    print("A1:", output1["answer"])

    # Ajouter dans l'historique
    chat_history.extend([HumanMessage(content=question1), AIMessage(content=output1["answer"])])

    # 2e question
    question2 = "Quels sont les cours associés ?"
    output2 = rag_graph.invoke({"input_question": question2, "chat_history": chat_history})
    print("Q2:", question2)
    print("A2:", output2["answer"])

    chat_history.extend([HumanMessage(content=question2), AIMessage(content=output2["answer"])])

# function to handle chat messages with retrieval-augmented generation (RAG) when using Langchain and ChromaDB.

from langchain_core.messages import HumanMessage, AIMessage  # Import the HumanMessage and AIMessage classes


def handle_chat_messages(chat_history, user_input, rag_chain):
    """
    Handle chat messages with retrieval-augmented generation (RAG).

    Args:
        chat_history (list): The chat history containing previous messages.
        user_input (str): The user's input message.
        llm: The language model instance.
        retriever: The retriever instance for fetching relevant context.
        contextualize_q_prompt: The prompt for contextualizing the question.
        qa_prompt: The prompt for the question-answering task.

    Returns:
        dict: A dictionary containing the generated response and updated chat history plus the relevant context used for the response.
    """

    # Invoke the RAG chain with the user input and chat history
    ai_response = rag_chain.invoke({"input": user_input, "chat_history": chat_history})

    # Update chat history with user input and AI response
    chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=ai_response["answer"])
    ])
    

    # PLACE HOLDER for context/sources and arranging it how we want to display it

    return {
        "response": ai_response["answer"],
        "chat_history": chat_history,
        "context": ai_response.get("context", [])
    }

def format_sources(context):
    sources = set()
    for doc in context:
        metadata = getattr(doc, "metadata", {})
        url = metadata.get("url", "").strip()
        source = metadata.get("source", "").strip()
        if url:
            sources.add(url)
        elif source:
            sources.add(source)
    return "\n".join(f"• {src}" for src in sources) if sources else "Aucune source identifiée"
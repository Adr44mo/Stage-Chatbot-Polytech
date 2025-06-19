# ==============================================================================
# Fonctions et routes pour la gestion de l'historique et des messages du chatbot
# ==============================================================================

# Imports des bibliothèques nécessaires
from fastapi import APIRouter, Depends, Header
from sqlmodel import Session, select
from typing import List
import json
# from langchain_core.messages import HumanMessage, AIMessage  

# Imports des modèles et outils
from .chat_models import Conversation, Message as DBMessage, ChatMessage
from .auth.database import get_session

# Initialisation du routeur API
router = APIRouter()

# # function to handle chat messages with retrieval-augmented generation (RAG) when using Langchain and ChromaDB.
# def handle_chat_messages(chat_history, user_input, rag_chain):
#     """
#     Handle chat messages with retrieval-augmented generation (RAG).

#     Args:
#         chat_history (list): The chat history containing previous messages.
#         user_input (str): The user's input message.
#         llm: The language model instance.
#         retriever: The retriever instance for fetching relevant context.
#         contextualize_q_prompt: The prompt for contextualizing the question.
#         qa_prompt: The prompt for the question-answering task.

#     Returns:
#         dict: A dictionary containing the generated response and updated chat history plus the relevant context used for the response.
#     """

#     # Invoke the RAG chain with the user input and chat history
#     ai_response = rag_chain.invoke({"input": user_input, "chat_history": chat_history})

#     # Update chat history with user input and AI response
#     chat_history.extend([
#         HumanMessage(content=user_input),
#         AIMessage(content=ai_response["answer"])
#     ])
    

#     # PLACE HOLDER for context/sources and arranging it how we want to display it

#     return {
#         "response": ai_response["answer"],
#         "chat_history": chat_history,
#         "context": ai_response.get("context", [])
#     }

# ===================================================================================
# Endpoint : récupération de l'historique de conversation pour un utilisateur anonyme
# ===================================================================================

@router.get("/history", response_model=List[ChatMessage])
def get_history(x_session_id: str = Header(...), session: Session = Depends(get_session)):
    """
    Récupère l'historique des messages (user/assistant) liés à un session_id anonyme.
    Retourne la liste des messages formatés pour le frontend.
    """
    conversation = session.exec(select(Conversation).where(Conversation.session_id == x_session_id)).first()
    if not conversation:
        return []
    messages = session.exec(select(DBMessage).where(DBMessage.conversation_id == conversation.id).order_by(DBMessage.timestamp)).all()
    return [
        ChatMessage(
            role=m.role,
            content=m.content,
            sources=json.loads(m.sources) if m.sources else [],
            timestamp=m.timestamp.isoformat() if m.timestamp else None
        )
        for m in messages
    ]

# =====================
# Fonctions utilitaires 
# =====================

def get_sources(context):
    """
    Extrait les sources (url ou chemin local) à partir des métadonnées du contexte RAG.
    Retourne une liste de chaînes uniques.
    """
    sources = set()
    for doc in context:
        metadata = getattr(doc, "metadata", {})
        url = metadata.get("source.url", "").strip()
        chemin_local = metadata.get("source.chemin_local", "").strip()
        if chemin_local:
            idx = chemin_local.find("/Document_handler")         # On garde un chemin relatif à partir de "/Document_handler"
            if idx != -1:
                chemin_local = chemin_local[idx:]
                print(f"Chemin local extrait : {chemin_local}")
        if url:
            sources.add(url)
        elif chemin_local:
            sources.add(chemin_local)
    return list(sources)

def get_or_create_conversation(session, session_id):
    """
    Récupère la conversation liée à un session_id, ou la crée si elle n'existe pas encore.
    """
    conversation = session.exec(select(Conversation).where(Conversation.session_id == session_id)).first()
    if not conversation:
        conversation = Conversation(session_id=session_id)
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    return conversation

def add_message(session, conversation_id, role, content, sources=None):
    """
    Ajoute un message (user ou assistant) à la conversation spécifiée.
    """
    if isinstance(sources, list):
        sources = json.dumps(sources)
    msg = DBMessage(conversation_id=conversation_id, role=role, content=content, sources=sources)
    session.add(msg)
    session.commit()
    return msg

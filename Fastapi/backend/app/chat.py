# ==============================================================================
# Fonctions et routes pour la gestion de l'historique et des messages du chatbot
# ==============================================================================

# Imports des bibliothèques nécessaires
from fastapi import APIRouter, Depends, Cookie
from sqlmodel import Session, select
from typing import List
import json
from color_utils import cp

# Imports des modèles et outils
from .chat_models import Conversation, Message as DBMessage, ChatMessage
from .database.database import get_session

# Initialisation du routeur API
router = APIRouter()

# ===================================================================================
# Endpoint : récupération de l'historique de conversation pour un utilisateur anonyme
# ===================================================================================

@router.get("/history", response_model=List[ChatMessage])
def get_history(polybot_session_id: str = Cookie(None), session: Session = Depends(get_session)):
    """
    Récupère l'historique des messages (user/assistant) liés à un session_id anonyme.
    Retourne la liste des messages formatés pour le frontend.
    """
    cp.print_debug(f"Fetching history for session: {polybot_session_id}")
    conversation = session.exec(select(Conversation).where(Conversation.session_id == polybot_session_id)).first()
    if not conversation:
        return []
    messages = session.exec(select(DBMessage).where(DBMessage.conversation_id == conversation.id).order_by(DBMessage.timestamp)).all()
    cp.print_debug(f"Retrieved {len(messages)} messages for session {polybot_session_id}")
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
    Prend le chemin local si c'est un PDF, l'URL si c'est un JSON.
    Retourne une liste de chaînes uniques.
    """
    sources = set()
    for doc in context:
        metadata = getattr(doc, "metadata", {})
        url = metadata.get("source.url", "").strip()
        chemin_local = metadata.get("source.chemin_local", "").strip()
        selected = None

        if chemin_local and chemin_local.endswith(".pdf"):
            idx = chemin_local.find("/Document_handler")
            if idx != -1:
                chemin_local = chemin_local[idx:]
            selected = chemin_local
        else:
            selected = url
        if selected:
            sources.add(selected)
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
    Affiche des informations de debug, notamment l'emplacement de la base de données.
    """

    # Debug : emplacement de la base de données
    db_url = str(session.bind.url) if hasattr(session.bind, "url") else "inconnue"
    cp.print_debug(f"Ajout d'un message dans la conversation {conversation_id} (role={role})")
    cp.print_debug(f"Emplacement de la base de données : {db_url}")

    if isinstance(sources, list):
        sources = json.dumps(sources)
    msg = DBMessage(conversation_id=conversation_id, role=role, content=content, sources=sources)
    session.add(msg)
    session.commit()
    cp.print_debug(f"Message ajouté avec l'ID {msg.id}")
    return msg

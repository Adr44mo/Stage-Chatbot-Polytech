# ===========================================================================
# Modèles et schémas pour la gestion des conversations et messages du chatbot
# ===========================================================================

# Imports des bibliothèques nécessaires
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel

# ==================================
# Modèles SQLModel (base de données)
# ==================================

class Conversation(SQLModel, table=True):
    """
    Représente une conversation anonyme liée à un utilisateur (session_id).
    Chaque conversation regroupe une suite de messages échangés.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List["Message"] = Relationship(back_populates="conversation")

class Message(SQLModel, table=True):
    """
    Représente un message individuel (utilisateur ou assistant) stocké en base.
    Contient le texte, le rôle (user/assistant), le timestamp et la relation à la conversation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    sources: Optional[str] = Field(default=None, description="Sources ou références associées au message, si applicable")

# ======================
# Schémas Pydantic (API)
# ======================

# Structure des données envoyées au frontend pour ne pas exposer d'infos internes (id, conversation_id). Permet de séparer la logique de persistance (DB) de la logique d'API (échange de données), on peut donc changer la structure de la base de données sans casser l'API :)

class MessageIn(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    sources: Optional[str] = None

class MessageOut(BaseModel):
    role: str
    content: str
    timestamp: str
    sources: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str
    chat_history: List[MessageIn]

class ChatResponse(BaseModel):
    answer: str
    sources: str

# ===========================================================================
# Modèles et schémas pour la gestion des conversations et messages du chatbot
# ===========================================================================

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel
from datetime import datetime
import datetime as dt

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

# ==================================
# Modèles RAG SQLModel (nouvelle architecture)
# ==================================

class RAGConversation(SQLModel, table=True):
    """
    Table RAG qui étend et complète les conversations existantes avec des métadonnées RAG.
    Utilise les relations avec Conversation et Message pour éviter la redondance.
    """
    __tablename__ = "rag_conversations_new"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(unique=True, index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relations vers les classes existantes
    conversation_id: int = Field(foreign_key="conversation.id")
    conversation: Optional[Conversation] = Relationship()
    
    # Question et réponse peuvent être récupérées via les relations Message
    # mais on les stocke ici pour les performances RAG
    question: str  # Dernière question de l'utilisateur
    answer: str    # Réponse générée par le RAG
    
    # Métadonnées RAG spécifiques
    intent_analysis: Optional[str] = Field(default=None, description="Analyse d'intention au format JSON")
    context_docs_count: int = Field(default=0, description="Nombre de documents utilisés comme contexte")
    sources_count: int = Field(default=0, description="Nombre de sources citées")
    processing_steps: Optional[str] = Field(default=None, description="Étapes de traitement RAG au format JSON")
    success: bool = Field(default=True, description="Succès de la génération RAG")
    error: Optional[str] = Field(default=None, description="Message d'erreur si échec")
    response_time: Optional[float] = Field(default=None, description="Temps de réponse en secondes")
    
    # Métriques de tokens
    user_input_tokens: int = Field(default=0)
    final_output_tokens: int = Field(default=0)
    intermediate_input_tokens: int = Field(default=0)
    intermediate_output_tokens: int = Field(default=0)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    grand_total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RAGTokenOperation(SQLModel, table=True):
    """
    Table des opérations de tokens liées aux conversations RAG.
    Correspond à la table token_operations de l'ancien système.
    """
    __tablename__ = "rag_token_operations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    rag_conversation_id: int = Field(foreign_key="rag_conversations_new.id")
    session_id: str = Field(index=True)
    operation: str = Field(description="Type d'opération: intent_analysis, answer_generation, etc.")
    model: str = Field(description="Modèle utilisé: gpt-4, gpt-3.5-turbo, etc.")
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relation vers la conversation RAG
    rag_conversation: Optional[RAGConversation] = Relationship()

class RAGContextDocument(SQLModel, table=True):
    """
    Table des documents contextuels utilisés dans une conversation RAG.
    Correspond à la table context_documents de l'ancien système.
    """
    __tablename__ = "rag_context_documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    rag_conversation_id: int = Field(foreign_key="rag_conversations_new.id")
    session_id: str = Field(index=True)
    content_preview: str = Field(description="Aperçu du contenu du document")
    metadonnee: str = Field(description="Métadonnées du document au format JSON")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relation vers la conversation RAG
    rag_conversation: Optional[RAGConversation] = Relationship()

# ==================================
# Modèles de statistiques RAG
# ==================================

class RAGDailyStats(SQLModel, table=True):
    """Statistiques journalières agrégées du système RAG"""
    __tablename__ = "rag_daily_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt.date = Field(unique=True, index=True)
    
    # Métriques de base
    total_conversations: int = Field(default=0)
    successful_conversations: int = Field(default=0)
    failed_conversations: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    
    # Métriques de tokens et coûts
    total_tokens: int = Field(default=0)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    
    # Métriques de performance
    avg_response_time: float = Field(default=0.0)
    min_response_time: float = Field(default=0.0)
    max_response_time: float = Field(default=0.0)
    
    # Métriques contextuelles
    total_context_docs: int = Field(default=0)
    total_sources: int = Field(default=0)
    avg_context_docs_per_conv: float = Field(default=0.0)
    avg_sources_per_conv: float = Field(default=0.0)
    
    # Distributions (JSON)
    intents_distribution: Optional[str] = Field(default=None, description="Distribution des intentions au format JSON")
    specialities_distribution: Optional[str] = Field(default=None, description="Distribution des spécialités au format JSON")
    
    # Métadonnées
    unique_sessions: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RAGMonthlyStats(SQLModel, table=True):
    """Statistiques mensuelles agrégées du système RAG"""
    __tablename__ = "rag_monthly_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    month: int = Field(index=True)
    
    # Contrainte d'unicité sur year/month
    __table_args__ = {"sqlite_autoincrement": True}
    
    # Métriques de base
    total_conversations: int = Field(default=0)
    successful_conversations: int = Field(default=0)
    failed_conversations: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    
    # Métriques de tokens et coûts
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    
    # Métriques de performance
    avg_response_time: float = Field(default=0.0)
    
    # Distributions (JSON)
    intents_distribution: Optional[str] = Field(default=None)
    specialities_distribution: Optional[str] = Field(default=None)
    
    # Métriques temporelles
    active_days: int = Field(default=0)
    avg_conversations_per_day: float = Field(default=0.0)
    peak_day: Optional[str] = Field(default=None)
    peak_day_conversations: int = Field(default=0)
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RAGYearlyStats(SQLModel, table=True):
    """Statistiques annuelles agrégées du système RAG"""
    __tablename__ = "rag_yearly_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(unique=True, index=True)
    
    # Métriques de base
    total_conversations: int = Field(default=0)
    successful_conversations: int = Field(default=0)
    failed_conversations: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    
    # Métriques de tokens et coûts
    total_tokens: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    
    # Métriques de performance
    avg_response_time: float = Field(default=0.0)
    
    # Distributions (JSON)
    intents_distribution: Optional[str] = Field(default=None)
    specialities_distribution: Optional[str] = Field(default=None)
    
    # Métriques temporelles
    active_months: int = Field(default=0)
    avg_conversations_per_month: float = Field(default=0.0)
    peak_month: Optional[int] = Field(default=None)
    peak_month_conversations: int = Field(default=0)
    
    # Évolution mensuelle (JSON)
    monthly_evolution: Optional[str] = Field(default=None, description="Évolution mois par mois au format JSON")
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ======================
# Schémas Pydantic (API)
# ======================

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    sources: Optional[List[str]] = None

class ChatRequest(BaseModel):
    prompt: str
    chat_history: List[ChatMessage]
    recaptcha_token: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

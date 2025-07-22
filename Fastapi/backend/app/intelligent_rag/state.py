"""
Intelligent RAG System - State Definitions
"""

from typing import TypedDict, List, Optional, Dict, Any, NotRequired
from enum import Enum
# Coûts des tokens pour le suivi des dépenses pour 1,000,000 tokens
INPUT_TOKEN_COST = 0.15  # Coût par token d'entrée
OUTPUT_TOKEN_COST = 0.6  # Coût par token de sortie

class IntentType(str, Enum):
    """Types d'intentions supportées"""
    DIRECT_ANSWER = "DIRECT_ANSWER"
    RAG_NEEDED = "RAG_NEEDED"
    SYLLABUS_SPECIFIC_COURSE = "SYLLABUS_SPECIFIC_COURSE"  # Question sur un cours spécifique
    SYLLABUS_SPECIALITY_OVERVIEW = "SYLLABUS_SPECIALITY_OVERVIEW"  # Question sur tous les cours d'une spé

class SpecialityType(str, Enum):
    """Spécialités disponibles à Polytech Sorbonne"""
    AGRAL = "AGRAL"  # Agroalimentaire
    EISE = "EISE"    # Électronique et Informatique - Systèmes Embarqués
    EI2I = "EI2I"    # Électronique et Informatique - Informatique Industrielle
    GM = "GM"        # Génie Mécanique
    MAIN = "MAIN"    # Mathématiques Appliquées et Informatique
    MTX = "MTX"      # Matériaux
    ROB = "ROB"      # Robotique
    ST = "ST"        # Sciences de la Terre
    GENERAL = "GENERAL"  # Pas de spécialité spécifique

class IntentAnalysisResult(TypedDict):
    """Résultat de l'analyse d'intention"""
    intent: IntentType
    speciality: Optional[SpecialityType]
    confidence: float
    reasoning: str
    needs_history: bool  # Nouveau champ pour déterminer si l'historique est nécessaire
    course_name: Optional[str]  # Nom du cours spécifique si applicable
    reformulation: Optional[str]  # Question reformulée si nécessaire

class TokenCostTrackerState(TypedDict):
    """État du tracker de coûts de tokens"""
    session_id: str  # ID de session pour le suivi des coûts
    prompt_tokens: int  # Nombre de tokens dans le prompt
    completion_tokens: int  # Nombre de tokens dans la réponse
    total_tokens: int  # Total des tokens utilisés
    model: str  # Nom du modèle utilisé
    operation: str  # Nom de l'opération (intent_analysis, rag_generation, etc.)

class IntelligentRAGState(TypedDict):
    """État du graphe RAG intelligent"""
    # Entrées obligatoires
    input_question: str
    chat_history: List[Dict[str, str]]
    
    # Champs optionnels avec NotRequired pour éviter les conflits LangGraph
    intent_analysis: NotRequired[Optional[IntentAnalysisResult]]
    retrieved_docs: NotRequired[Optional[List[Any]]]
    filtered_docs: NotRequired[Optional[List[Any]]]
    answer: NotRequired[Optional[str]]
    context: NotRequired[Optional[List[Any]]]
    sources: NotRequired[Optional[List[str]]]
    processing_steps: NotRequired[List[str]]
    error: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]  # Pour le tracking des coûts
    token_tracker: NotRequired[Optional[List[TokenCostTrackerState]]]  # Instance du token tracker


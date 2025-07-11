"""
Intelligent RAG System - State Definitions
"""

from typing import TypedDict, List, Optional, Dict, Any, NotRequired
from enum import Enum

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

"""
FastAPI Integration for Intelligent RAG System
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from .graph import invoke_intelligent_rag
from .db_logger import rag_db_logger

# Import des modèles existants pour compatibilité
from ..chat_models import ChatRequest, ChatResponse, ChatMessage

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

router = APIRouter(prefix="/intelligent-rag", tags=["Intelligent RAG"])

class ChatMessage(BaseModel):
    role: str
    content: str

class IntelligentRAGRequest(BaseModel):
    question: str
    chat_history: Optional[List[ChatMessage]] = []

class IntelligentRAGResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]
    sources: List[str]
    intent_analysis: Optional[Dict[str, Any]]
    processing_steps: List[str]
    success: bool
    error: Optional[str]
    response_time: float
    session_id: Optional[str]
    token_cost: Optional[Dict[str, Any]] = None  # Ajout du coût des tokens

@router.post("/chat_intelligent", response_model=IntelligentRAGResponse)
async def intelligent_rag_chat(request: IntelligentRAGRequest):
    """
    Endpoint pour le chat avec RAG intelligent
    """
    try:
        # Convertir l'historique en format dict
        chat_history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
        
        # Invoquer le système RAG intelligent
        result = invoke_intelligent_rag(request.question, chat_history)
        
        return IntelligentRAGResponse(
            answer=result["answer"],
            context=result.get("context", []),
            sources=result.get("sources", []),
            intent_analysis=result.get("intent_analysis"),
            processing_steps=result.get("processing_steps", []),
            success=result["success"],
            error=result.get("error"),
            response_time=result.get("response_time", 0.0),
            session_id=result.get("session_id")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur du système RAG intelligent: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Vérification de l'état du système
    """
    try:
        # Test simple
        result = invoke_intelligent_rag("Test de santé du système")
        return {
            "status": "healthy",
            "message": "Système RAG intelligent opérationnel",
            "test_success": result["success"],
            "response_time": result.get("response_time", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Système indisponible: {str(e)}")

# ================================
# ENDPOINTS COMPATIBLES AVEC L'API EXISTANTE
# ================================

@router.post("/chat", response_model=ChatResponse)
async def intelligent_rag_chat_compatible(request: ChatRequest):
    """
    Endpoint compatible avec l'API existante (/chat)
    Utilise le même format de requête et réponse que l'API classique
    """
    try:
        # Convertir l'historique en format dict
        chat_history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
        
        # Invoquer le système RAG intelligent
        result = invoke_intelligent_rag(request.prompt, chat_history)
        
        # Retourner uniquement les champs compatibles avec ChatResponse
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur du système RAG intelligent: {str(e)}")

# Export pour intégration dans l'API principale
__all__ = ["router", "invoke_intelligent_rag"]

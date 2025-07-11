"""
FastAPI Integration for Intelligent RAG System
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from .graph import invoke_intelligent_rag
from .logger import rag_logger

# Import des modèles existants pour compatibilité
from ..chat_models import ChatRequest, ChatResponse, ChatMessage

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

class StatisticsResponse(BaseModel):
    total_requests: int
    total_tokens: Dict[str, int]
    intents: Dict[str, int]
    specialities: Dict[str, int]
    estimated_cost: Dict[str, float]
    performance: Optional[Dict[str, float]]
    errors: int
    last_updated: Optional[str]

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

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Obtenir les statistiques complètes du système
    """
    try:
        stats = rag_logger.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération statistiques: {str(e)}")

@router.get("/statistics/daily")
async def get_daily_statistics(date: Optional[str] = Query(None, description="Date au format YYYY-MM-DD")):
    """
    Obtenir les statistiques journalières
    """
    try:
        if date:
            # Valider le format de date
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")
        
        daily_stats = rag_logger.get_daily_report(date)
        return {
            "date": date or datetime.now().strftime('%Y-%m-%d'),
            "statistics": daily_stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération statistiques journalières: {str(e)}")

@router.post("/maintenance/cleanup")
async def cleanup_old_logs(days_to_keep: int = Query(30, ge=1, le=365, description="Nombre de jours à conserver")):
    """
    Nettoyer les anciens logs
    """
    try:
        deleted_count = rag_logger.cleanup_old_logs(days_to_keep)
        return {
            "message": f"{deleted_count} anciens logs supprimés",
            "days_kept": days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage logs: {str(e)}")

@router.get("/logs/recent")
async def get_recent_logs(limit: int = Query(10, ge=1, le=100, description="Nombre de logs récents à retourner")):
    """
    Obtenir les logs récents
    """
    try:
        logs_dir = rag_logger.responses_dir
        log_files = sorted(logs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        recent_logs = []
        for log_file in log_files[:limit]:
            try:
                import json
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    # Inclure seulement les informations essentielles
                    recent_logs.append({
                        "session_id": log_data.get("session_id"),
                        "timestamp": log_data.get("timestamp"),
                        "question": log_data["request"]["question"][:100] + "..." if len(log_data["request"]["question"]) > 100 else log_data["request"]["question"],
                        "intent": log_data["response"]["intent_analysis"]["intent"] if log_data["response"]["intent_analysis"] else None,
                        "success": log_data["response"]["success"],
                        "response_time": log_data["performance"]["response_time_seconds"],
                        "tokens": log_data["performance"]["tokens"]["total"]
                    })
            except Exception as e:
                print(f"Erreur lecture log {log_file}: {e}")
                continue
        
        return {
            "recent_logs": recent_logs,
            "total_logs_found": len(log_files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération logs récents: {str(e)}")

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

@router.post("/chat_detailed", response_model=IntelligentRAGResponse)
async def intelligent_rag_chat_detailed(request: ChatRequest):
    """
    Endpoint détaillé qui retourne toutes les informations du système intelligent
    Utilise le même format de requête que l'API existante, mais retourne plus d'infos
    """
    try:
        # Convertir l'historique en format dict
        chat_history = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
        
        # Invoquer le système RAG intelligent
        result = invoke_intelligent_rag(request.prompt, chat_history)
        
        return IntelligentRAGResponse(
            answer=result["answer"],
            context=result.get("context", []),
            sources=result.get("sources", []),
            intent_analysis=result.get("intent_analysis"),
            processing_steps=result.get("processing_steps", []),
            success=result["success"],
            error=result.get("error"),
            response_time=result.get("response_time", 0.0),
            session_id=result.get("session_id"),
            token_cost=result.get("token_cost")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur du système RAG intelligent: {str(e)}")

# Export pour intégration dans l'API principale
__all__ = ["router", "invoke_intelligent_rag"]

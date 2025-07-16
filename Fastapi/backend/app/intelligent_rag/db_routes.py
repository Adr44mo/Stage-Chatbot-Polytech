"""
Routes API pour la base de données RAG
"""

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .database import rag_database
from .db_logger import rag_db_logger

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

router = APIRouter(prefix="/intelligent-rag/database", tags=["Database RAG"])

# ================================
# MODÈLES PYDANTIC
# ================================

class ConversationSummary(BaseModel):
    session_id: str
    timestamp: str
    question: str
    answer_preview: str
    intent: Optional[str]
    success: bool
    response_time: Optional[float]
    total_tokens: int
    cost_usd: float

class ConversationDetail(BaseModel):
    session_id: str
    timestamp: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    performance: Dict[str, Any]
    context: Dict[str, Any]

class DatabaseStatistics(BaseModel):
    total_requests: int
    total_tokens: Dict[str, int]
    intents: Dict[str, int]
    specialities: Dict[str, int]
    estimated_cost: Dict[str, float]
    performance: Dict[str, float]
    errors: int
    daily_stats: Dict[str, Any]
    last_updated: str

class DailyReport(BaseModel):
    date: str
    requests: int
    tokens: Dict[str, int]
    cost_usd: float
    avg_response_time: float
    errors: int
    intents: Dict[str, int]

class DatabaseInfo(BaseModel):
    database_path: str
    database_size_mb: float
    tables: Dict[str, int]
    date_range: Dict[str, Optional[str]]

class TokenAnalysis(BaseModel):
    session_id: str
    operations: List[Dict[str, Any]]
    total_cost: float
    total_tokens: int

# ================================
# ROUTES DE BASE
# ================================

@router.get("/info", response_model=DatabaseInfo)
async def get_database_info():
    """Obtenir des informations sur la base de données"""
    try:
        info = rag_database.get_database_info()
        return DatabaseInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération infos DB: {str(e)}")

@router.get("/health")
async def database_health():
    """Vérifier l'état de la base de données"""
    try:
        # Test simple de connexion
        stats = rag_database.get_statistics()
        return {
            "status": "healthy",
            "message": "Base de données opérationnelle",
            "total_conversations": stats.get("total_requests", 0),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Base de données indisponible: {str(e)}")

# ================================
# GESTION DES CONVERSATIONS
# ================================

@router.get("/conversations/recent", response_model=List[ConversationSummary])
async def get_recent_conversations(limit: int = Query(10, ge=1, le=100)):
    """Récupérer les conversations récentes"""
    try:
        conversations = rag_database.get_recent_conversations(limit)
        return [ConversationSummary(**conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération conversations: {str(e)}")

@router.get("/conversations/{session_id}", response_model=ConversationDetail)
async def get_conversation(session_id: str = Path(..., description="ID de la session")):
    """Récupérer une conversation complète"""
    try:
        conversation = rag_database.get_conversation(session_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")
        return ConversationDetail(**conversation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération conversation: {str(e)}")

@router.get("/conversations/search")
async def search_conversations(
    query: str = Query(..., description="Terme à rechercher"),
    limit: int = Query(10, ge=1, le=100)
):
    """Rechercher des conversations par contenu"""
    try:
        # Note: Cette recherche nécessiterait une extension de la base de données
        # Pour l'instant, retour basique
        return {
            "query": query,
            "message": "Recherche textuelle pas encore implémentée - extension future",
            "suggestions": [
                "Utiliser les filtres par date",
                "Filtrer par intention",
                "Utiliser les conversations récentes"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche: {str(e)}")

@router.get("/conversations/by-intent/{intent}")
async def get_conversations_by_intent(
    intent: str = Path(..., description="Type d'intention"),
    limit: int = Query(10, ge=1, le=100)
):
    """Récupérer les conversations par intention"""
    try:
        # Cette fonctionnalité nécessiterait une requête spécialisée
        # Pour l'instant, retour basique
        return {
            "intent": intent,
            "message": "Filtrage par intention - extension future",
            "available_intents": [
                "DIRECT_ANSWER",
                "RAG_NEEDED", 
                "SYLLABUS_SPECIFIC_COURSE",
                "SYLLABUS_SPECIALITY_OVERVIEW"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur filtrage par intention: {str(e)}")

# ================================
# STATISTIQUES ET ANALYTICS
# ================================

@router.get("/statistics", response_model=DatabaseStatistics)
async def get_statistics():
    """Obtenir les statistiques complètes"""
    try:
        stats = rag_database.get_statistics()
        return DatabaseStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération statistiques: {str(e)}")

@router.get("/statistics/daily", response_model=DailyReport)
async def get_daily_report(date: Optional[str] = Query(None, description="Date YYYY-MM-DD")):
    """Obtenir le rapport journalier"""
    try:
        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date invalide (YYYY-MM-DD)")
        
        report = rag_database.get_daily_report(date)
        if not report:
            report = {
                "requests": 0,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "cost_usd": 0.0,
                "avg_response_time": 0.0,
                "errors": 0,
                "intents": {}
            }
        
        return DailyReport(
            date=date or datetime.now().strftime('%Y-%m-%d'),
            **report
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur rapport journalier: {str(e)}")

@router.get("/statistics/range")
async def get_statistics_range(
    start_date: str = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Date de fin (YYYY-MM-DD)")
):
    """Obtenir les statistiques sur une période"""
    try:
        # Valider les dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Format de date invalide (YYYY-MM-DD)")
        
        if start > end:
            raise HTTPException(status_code=400, detail="Date de début après date de fin")
        
        # Calculer les statistiques pour la période
        range_stats = []
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_report = rag_database.get_daily_report(date_str)
            if daily_report and daily_report.get("requests", 0) > 0:
                range_stats.append({
                    "date": date_str,
                    **daily_report
                })
            current_date += timedelta(days=1)
        
        # Calculer les totaux
        total_requests = sum(day["requests"] for day in range_stats)
        total_tokens = sum(day["tokens"]["total"] for day in range_stats)
        total_cost = sum(day["cost_usd"] for day in range_stats)
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": len(range_stats)
            },
            "totals": {
                "requests": total_requests,
                "tokens": total_tokens,
                "cost_usd": total_cost
            },
            "daily_data": range_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur statistiques période: {str(e)}")

@router.get("/analytics/tokens")
async def get_token_analytics(
    days: int = Query(7, ge=1, le=90, description="Nombre de jours à analyser")
):
    """Analyse des tokens sur une période"""
    try:
        # Cette fonctionnalité nécessiterait des requêtes spécialisées
        return {
            "message": "Analyse des tokens - extension future",
            "period_days": days,
            "features": [
                "Évolution des tokens par jour",
                "Répartition par type d'opération",
                "Coût par spécialité",
                "Efficiency metrics"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse tokens: {str(e)}")

# ================================
# GESTION ET MAINTENANCE
# ================================

@router.post("/maintenance/cleanup")
async def cleanup_database(
    days_to_keep: int = Query(30, ge=1, le=365, description="Jours à conserver")
):
    """Nettoyer les anciennes données"""
    try:
        deleted_count = rag_database.cleanup_old_data(days_to_keep)
        return {
            "message": f"{deleted_count} conversations supprimées",
            "days_kept": days_to_keep,
            "cleanup_date": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage: {str(e)}")

@router.post("/maintenance/clean_all")
async def clean_all_data():
    """Nettoyer toutes les données de la base"""
    try:
        rag_database.clean_all_data()
        return {
            "message": "Toutes les données ont été supprimées",
            "cleanup_date": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur nettoyage complet: {str(e)}")

@router.get("/maintenance/backup")
async def backup_database():
    """Créer une sauvegarde de la base de données"""
    try:
        # Cette fonctionnalité nécessiterait l'implémentation d'un système de backup
        return {
            "message": "Système de sauvegarde - extension future",
            "recommendations": [
                "Sauvegarde automatique quotidienne",
                "Export CSV/JSON",
                "Réplication base de données"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde: {str(e)}")

@router.get("/export/csv")
async def export_conversations_csv(
    days: int = Query(7, ge=1, le=90, description="Nombre de jours à exporter")
):
    """Exporter les conversations en CSV"""
    try:
        # Cette fonctionnalité nécessiterait l'implémentation d'un export CSV
        return {
            "message": "Export CSV - extension future",
            "period_days": days,
            "format": "CSV avec colonnes: session_id, timestamp, question, answer, intent, tokens, cost"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur export CSV: {str(e)}")

# ================================
# MÉTRIQUES AVANCÉES
# ================================

@router.get("/metrics/performance")
async def get_performance_metrics():
    """Métriques de performance du système"""
    try:
        stats = rag_database.get_statistics()
        performance = stats.get("performance", {})
        
        return {
            "response_time": {
                "average": performance.get("avg_response_time", 0),
                "min": performance.get("min_response_time", 0),
                "max": performance.get("max_response_time", 0)
            },
            "success_rate": {
                "total_requests": stats.get("total_requests", 0),
                "errors": stats.get("errors", 0),
                "success_rate": (stats.get("total_requests", 0) - stats.get("errors", 0)) / max(stats.get("total_requests", 1), 1)
            },
            "token_efficiency": {
                "total_tokens": stats.get("total_tokens", {}).get("total", 0),
                "avg_tokens_per_request": stats.get("total_tokens", {}).get("total", 0) / max(stats.get("total_requests", 1), 1)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur métriques performance: {str(e)}")

@router.get("/metrics/costs")
async def get_cost_metrics():
    """Métriques de coût du système"""
    try:
        stats = rag_database.get_statistics()
        
        return {
            "total_cost": stats.get("estimated_cost", {}).get("total_cost_usd", 0),
            "average_cost_per_request": stats.get("estimated_cost", {}).get("total_cost_usd", 0) / max(stats.get("total_requests", 1), 1),
            "token_breakdown": stats.get("total_tokens", {}),
            "trends": "Analyse des tendances - extension future"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur métriques coût: {str(e)}")

# Export pour intégration
__all__ = ["router"]

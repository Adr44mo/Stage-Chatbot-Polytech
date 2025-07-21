"""
Routes API simplifiées pour la base de données RAG utilisant SQLModel
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, func
from typing import List, Dict, Any
from datetime import datetime
from .database import get_session
from .models import RAGConversation, RAGTokenOperation, RAGContextDocument

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

router = APIRouter(prefix="/intelligent-rag/database", tags=["Database RAG"])

# ================================
# ROUTES BASIQUES
# ================================

@router.get("/health")
def health_check():
    """Vérification de santé de la base de données"""
    return {
        "status": "healthy",
        "message": "Base de données RAG opérationnelle",
        "timestamp": datetime.utcnow().isoformat(),
        "architecture": "SQLModel with RAGConversation, RAGTokenOperation, RAGContextDocument"
    }

@router.get("/stats/basic")
def get_basic_stats(session: Session = Depends(get_session)):
    """Statistiques de base utilisant SQLModel"""
    try:
        # Compter les conversations RAG
        total_conversations = session.exec(
            select(func.count(RAGConversation.id))
        ).one()
        
        # Compter les opérations de tokens
        total_operations = session.exec(
            select(func.count(RAGTokenOperation.id))
        ).one()
        
        # Compter les documents contextuels
        total_documents = session.exec(
            select(func.count(RAGContextDocument.id))
        ).one()
        
        # Calculs des coûts totaux
        total_cost = session.exec(
            select(func.sum(RAGConversation.total_cost_usd))
        ).one() or 0.0
        
        # Calculs des tokens totaux
        total_tokens = session.exec(
            select(func.sum(RAGConversation.grand_total_tokens))
        ).one() or 0
        
        return {
            "total_conversations": total_conversations,
            "total_token_operations": total_operations,
            "total_context_documents": total_documents,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        cp.print_error(f"Erreur lors du calcul des statistiques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur calcul statistiques: {str(e)}")

@router.get("/conversations/recent")
def get_recent_conversations(limit: int = 10, session: Session = Depends(get_session)):
    """Récupérer les conversations RAG récentes"""
    try:
        conversations = session.exec(
            select(RAGConversation)
            .order_by(RAGConversation.timestamp.desc())
            .limit(limit)
        ).all()
        
        result = []
        for conv in conversations:
            result.append({
                "id": conv.id,
                "session_id": conv.session_id,
                "timestamp": conv.timestamp.isoformat(),
                "question": conv.question[:100] + "..." if len(conv.question) > 100 else conv.question,
                "answer_preview": conv.answer[:100] + "..." if len(conv.answer) > 100 else conv.answer,
                "success": conv.success,
                "total_tokens": conv.grand_total_tokens,
                "cost_usd": conv.total_cost_usd,
                "context_docs_count": conv.context_docs_count,
                "sources_count": conv.sources_count
            })
        
        return {
            "conversations": result,
            "count": len(result),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        cp.print_error(f"Erreur lors de la récupération des conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération conversations: {str(e)}")

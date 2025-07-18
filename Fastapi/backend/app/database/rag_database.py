"""
Interface de compatibilité pour le système RAG intelligent
Redirige vers la base de données unifiée
"""

from .database import unified_database
from typing import Dict, Any, Optional, List

class RAGDatabase:
    """Interface de compatibilité pour l'ancien système RAG"""
    
    def __init__(self, db_path: str = None):
        # On utilise l'instance unifiée existante
        self._unified_db = unified_database
    
    def save_conversation(self, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Sauvegarder une conversation - redirige vers la DB unifiée"""
        return self._unified_db.save_rag_conversation(session_id, conversation_data)
    
    def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une conversation - redirige vers la DB unifiée"""
        return self._unified_db.get_rag_conversation(session_id)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les conversations récentes - redirige vers la DB unifiée"""
        return self._unified_db.get_recent_rag_conversations(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculer les statistiques - redirige vers la DB unifiée"""
        return self._unified_db.get_rag_statistics()
    
    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Obtenir le rapport journalier - utilise les statistiques générales"""
        stats = self._unified_db.get_rag_statistics()
        if date and date in stats.get("daily_stats", {}):
            return stats["daily_stats"][date]
        return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Nettoyer les anciennes données - redirige vers la DB unifiée"""
        return self._unified_db.cleanup_old_rag_data(days_to_keep)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtenir des informations sur la base de données - redirige vers la DB unifiée"""
        return self._unified_db.get_database_info()
    
    def clean_all_data(self) -> None:
        """Nettoyer toutes les données RAG"""
        # On peut implémenter cela si nécessaire
        pass

# Instance globale de compatibilité
rag_database = RAGDatabase()
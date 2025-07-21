"""
Interface de compatibilité temporaire pour l'ancien système RAG
Utilise maintenant SQLModel au lieu de unified_database
"""

from typing import Dict, Any, Optional, List

class RAGDatabase:
    """Interface de compatibilité temporaire - DEPRECATED"""
    
    def __init__(self, db_path: str = None):
        # Cette classe est maintenant obsolète
        # Utilisez directement SQLModel avec les modèles RAGConversation, etc.
        pass
    
    def save_conversation(self, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """DEPRECATED - Utilisez update_rag_conversation() dans db_update_stat.py"""
        return False
    
    def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """DEPRECATED - Utilisez SQLModel directement"""
        return None
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """DEPRECATED - Utilisez SQLModel directement"""
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """DEPRECATED - Utilisez SQLModel directement"""
        return {}
    
    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """DEPRECATED - Utilisez SQLModel directement"""
        return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """DEPRECATED - Utilisez SQLModel directement"""
        return 0
    
    def get_database_info(self) -> Dict[str, Any]:
        """DEPRECATED - Utilisez SQLModel directement"""
        return {"message": "Cette interface est obsolète. Utilisez SQLModel directement."}

# Instance de compatibilité temporaire
rag_database = RAGDatabase()

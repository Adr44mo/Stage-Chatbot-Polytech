"""
Logger RAG avec base de données SQLite
"""

import tiktoken
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from .database import rag_database
from .token_tracker import token_tracker

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

class RAGDatabaseLogger:
    """Logger RAG utilisant SQLite au lieu de JSON"""
    
    def __init__(self):
        # Initialiser le tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
        except Exception:
            # Fallback si le modèle n'est pas reconnu
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Compter les tokens dans un texte"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            cp.print_error(f"[Logger] Erreur comptage tokens: {e}")
            # Estimation approximative : ~4 caractères par token
            return len(text) // 4
    
    def generate_session_id(self, question: str, timestamp: str) -> str:
        """Générer un ID unique pour la session"""
        content = f"{question}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def log_conversation(self, 
                        question: str,
                        result: Dict[str, Any],
                        chat_history: list = None,
                        response_time: float = None,
                        intermediate_operations: list = None) -> str:
        """
        Logger une conversation complète dans la base de données
        
        Args:
            question: Question de l'utilisateur
            result: Résultat du RAG
            chat_history: Historique de conversation
            response_time: Temps de réponse
            intermediate_operations: Liste des opérations intermédiaires avec leurs coûts
        
        Returns:
            str: ID du session créé
        """
        timestamp = datetime.now()
        session_id = self.generate_session_id(question, timestamp.isoformat())
        
        # Compter les tokens de base (utilisateur)
        input_tokens = self.count_tokens(question)
        if chat_history:
            history_text = " ".join([msg.get("content", "") for msg in chat_history])
            input_tokens += self.count_tokens(history_text)
        
        output_tokens = self.count_tokens(result.get("answer", ""))
        
        # Calculer les tokens des opérations intermédiaires
        intermediate_tokens = {
            "total_input": 0,
            "total_output": 0,
            "operations": []
        }
        
        # Récupérer les opérations depuis le token_tracker
        if session_id in token_tracker.conversations:
            conversation_cost = token_tracker.conversations[session_id]
            intermediate_operations = []
            
            for op in conversation_cost.operations:
                operation_data = {
                    "operation": op.operation,
                    "model": op.model,
                    "input_tokens": op.prompt_tokens,
                    "output_tokens": op.completion_tokens,
                    "total_tokens": op.total_tokens,
                    "cost_usd": 0.0,  # Calculé par le token_tracker
                    "timestamp": op.timestamp.isoformat()
                }
                
                # Calculer le coût
                if op.model in token_tracker.pricing:
                    cost_usd = (op.prompt_tokens * token_tracker.pricing[op.model]["input"] / 1000) + \
                              (op.completion_tokens * token_tracker.pricing[op.model]["output"] / 1000)
                    operation_data["cost_usd"] = cost_usd
                
                intermediate_operations.append(operation_data)
                intermediate_tokens["total_input"] += op.prompt_tokens
                intermediate_tokens["total_output"] += op.completion_tokens
        
        if intermediate_operations:
            intermediate_tokens["operations"] = intermediate_operations
        
        # Calculer les tokens totaux (utilisateur + intermédiaires)
        total_input_tokens = input_tokens + intermediate_tokens["total_input"]
        total_output_tokens = output_tokens + intermediate_tokens["total_output"]
        total_tokens = total_input_tokens + total_output_tokens
        
        # Calculer le coût total
        total_cost = sum(op.get("cost_usd", 0) for op in intermediate_operations or [])
        
        # Préparer les données pour la base de données
        conversation_data = {
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "request": {
                "question": question,
                "chat_history": chat_history or [],
                "user_input_tokens": input_tokens
            },
            "response": {
                "answer": result.get("answer", ""),
                "intent_analysis": result.get("intent_analysis"),
                "context_docs_count": len(result.get("context", [])),
                "sources_count": len(result.get("sources", [])),
                "processing_steps": result.get("processing_steps", []),
                "final_output_tokens": output_tokens,
                "success": result.get("success", False),
                "error": result.get("error")
            },
            "performance": {
                "response_time_seconds": response_time,
                "tokens": {
                    "user_input": input_tokens,
                    "final_output": output_tokens,
                    "intermediate_input": intermediate_tokens["total_input"],
                    "intermediate_output": intermediate_tokens["total_output"],
                    "total_input": total_input_tokens,
                    "total_output": total_output_tokens,
                    "grand_total": total_tokens
                },
                "cost": {
                    "total_usd": total_cost,
                    "operations": intermediate_tokens["operations"]
                }
            },
            "context": {
                "documents": [
                    {
                        "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    } for doc in result.get("context", [])
                ]
            }
        }
        
        # Sauvegarder dans la base de données
        success = rag_database.save_conversation(session_id, conversation_data)
        
        if success:
            cp.print_success(f"[Logger] Conversation {session_id} sauvegardée en base")
        else:
            cp.print_error(f"[Logger] Erreur sauvegarde conversation {session_id}")
        
        return session_id
    
    def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une conversation"""
        return rag_database.get_conversation(session_id)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les conversations récentes"""
        return rag_database.get_recent_conversations(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques complètes"""
        return rag_database.get_statistics()
    
    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Obtenir le rapport journalier"""
        return rag_database.get_daily_report(date)
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Nettoyer les anciennes données"""
        return rag_database.cleanup_old_data(days_to_keep)
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtenir des informations sur la base de données"""
        return rag_database.get_database_info()

# Instance globale du logger avec base de données
rag_db_logger = RAGDatabaseLogger()

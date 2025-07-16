"""
Token Cost Tracking System - Suivi des coûts de tokens pour tous les appels OpenAI
"""

import functools
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import tiktoken

@dataclass
class TokenUsage:
    """Représente l'utilisation de tokens pour un appel"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    timestamp: datetime
    operation: str  # "intent_analysis", "rag_generation", "direct_answer", etc.

@dataclass
class ConversationCost:
    """Coût total d'une conversation"""
    session_id: str
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    operations: List[TokenUsage] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

class TokenCostTracker:
    """Tracker pour calculer les coûts de tokens de tous les appels OpenAI"""
    
    def __init__(self):
        self.conversations: Dict[str, ConversationCost] = {}
        
        # Prix OpenAI (en USD par 1000 tokens) - Mise à jour régulière requise
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "text-embedding-ada-002": {"input": 0.0001, "output": 0.0},
            "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
            "text-embedding-3-large": {"input": 0.00013, "output": 0.0}
        }
    
    def start_conversation(self, session_id: str) -> None:
        """Démarre le tracking pour une nouvelle conversation"""
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationCost(session_id=session_id)
    
    def track_usage(self, session_id: str, prompt_tokens: int, completion_tokens: int, 
                   model: str, operation: str) -> TokenUsage:
        """Enregistre l'utilisation de tokens pour un appel"""
        if session_id not in self.conversations:
            self.start_conversation(session_id)
        
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
            timestamp=datetime.now(),
            operation=operation
        )
        
        # Ajouter à la conversation
        conv = self.conversations[session_id]
        conv.operations.append(usage)
        conv.total_prompt_tokens += prompt_tokens
        conv.total_completion_tokens += completion_tokens
        conv.total_tokens += prompt_tokens + completion_tokens
        
        # Calculer le coût
        if model in self.pricing:
            cost = (prompt_tokens * self.pricing[model]["input"] / 1000) + \
                   (completion_tokens * self.pricing[model]["output"] / 1000)
            conv.total_cost_usd += cost
        
        return usage
    
    def end_conversation(self, session_id: str) -> ConversationCost:
        """Finalise le tracking d'une conversation"""
        if session_id in self.conversations:
            self.conversations[session_id].end_time = datetime.now()
            return self.conversations[session_id]
        return None
    
    def get_conversation_cost(self, session_id: str) -> Optional[ConversationCost]:
        """Récupère le coût d'une conversation"""
        return self.conversations.get(session_id)
    
    def estimate_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """Estime le nombre de tokens dans un texte"""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback : approximation grossière
            return len(text) // 4
    
    def estimate_prompt_tokens(self, state: dict, model: str) -> int:
        """Estimation des tokens pour les prompts système"""
        prompt_tokens = 0
        
        # Tokens pour les prompts système de base
        system_prompts = [
            "Vous êtes un assistant spécialisé dans l'aide aux étudiants de Polytech.",
            "Analysez la question et déterminez si elle porte sur un cours spécifique.",
            "Répondez de manière claire et structurée."
        ]
        
        for prompt in system_prompts:
            prompt_tokens += self.estimate_tokens(prompt, model)
        
        # Tokens pour les instructions spécifiques selon le type de question
        if state.get("is_course_question"):
            course_prompt = "Répondez spécifiquement à cette question de cours en utilisant le contexte fourni."
            prompt_tokens += self.estimate_tokens(course_prompt, model)
        
        return prompt_tokens
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques globales"""
        total_conversations = len(self.conversations)
        total_cost = sum(conv.total_cost_usd for conv in self.conversations.values())
        total_tokens = sum(conv.total_tokens for conv in self.conversations.values())
        
        # Statistiques par opération
        operation_stats = {}
        for conv in self.conversations.values():
            for op in conv.operations:
                if op.operation not in operation_stats:
                    operation_stats[op.operation] = {
                        "count": 0,
                        "total_tokens": 0,
                        "avg_tokens": 0
                    }
                operation_stats[op.operation]["count"] += 1
                operation_stats[op.operation]["total_tokens"] += op.total_tokens
        
        # Calculer les moyennes
        for op_name, stats in operation_stats.items():
            stats["avg_tokens"] = stats["total_tokens"] / stats["count"]
        
        return {
            "total_conversations": total_conversations,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "avg_cost_per_conversation": total_cost / total_conversations if total_conversations > 0 else 0,
            "operation_stats": operation_stats
        }
    
    def get_session_operations(self, session_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les opérations d'une session"""
        if session_id not in self.conversations:
            return []
        
        conv = self.conversations[session_id]
        operations = []
        
        for op in conv.operations:
            # Calculer le coût pour cette opération
            cost_usd = 0
            if op.model in self.pricing:
                cost_usd = (op.prompt_tokens * self.pricing[op.model]["input"] / 1000) + \
                          (op.completion_tokens * self.pricing[op.model]["output"] / 1000)
            
            operations.append({
                "operation": op.operation,
                "model": op.model,
                "prompt_tokens": op.prompt_tokens,
                "completion_tokens": op.completion_tokens,
                "total_tokens": op.total_tokens,
                "cost_usd": cost_usd,
                "timestamp": op.timestamp.isoformat()
            })
        
        return operations

# Instance globale du tracker
token_tracker = TokenCostTracker()

def track_openai_call(operation: str, model: str = None):
    """Décorateur pour tracker automatiquement les appels OpenAI"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extraire session_id du state si disponible
            session_id = "unknown"
            if args and hasattr(args[0], 'get'):
                state = args[0]
                session_id = state.get("session_id", "unknown")
            
            # Récupérer le vrai modèle utilisé
            actual_model = model
            if not actual_model:
                # Tenter de récupérer le modèle depuis llm
                try:
                    from ..llmm import llm
                    actual_model = getattr(llm, 'model_name', 'gpt-4o-mini')
                except:
                    actual_model = "gpt-4o-mini"
            
            # Calculer les tokens d'entrée plus précisément
            input_text = ""
            if args and hasattr(args[0], 'get'):
                state = args[0]
                input_text = state.get("input_question", "")
                
                # Ajouter l'historique de conversation si présent
                if state.get("chat_history"):
                    history_text = "\n".join([
                        f"User: {msg['content']}" if msg['role'] == "user" else f"Assistant: {msg['content']}"
                        for msg in state["chat_history"]
                    ])
                    input_text += f"\n\nHistorique:\n{history_text}"
                
                # Ajouter les documents RAG si présents
                if state.get("retrieved_docs"):
                    docs_text = "\n\n".join([
                        doc.page_content for doc in state["retrieved_docs"][:6]
                    ])
                    input_text += f"\n\nContexte RAG:\n{docs_text}"
            
            # Estimer les tokens d'entrée avec le contenu complet
            prompt_tokens = token_tracker.estimate_tokens(input_text, actual_model)
            
            # Ajouter les tokens des prompts système
            if args and hasattr(args[0], 'get'):
                system_prompt_tokens = token_tracker.estimate_prompt_tokens(args[0], actual_model)
                prompt_tokens += system_prompt_tokens
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Estimer les tokens de sortie
            output_text = ""
            if isinstance(result, dict):
                output_text = result.get("answer", "")
            
            completion_tokens = token_tracker.estimate_tokens(output_text, actual_model)
            
            # Enregistrer l'utilisation
            token_tracker.track_usage(
                session_id=session_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=actual_model,
                operation=operation
            )
            
            return result
        return wrapper
    return decorator

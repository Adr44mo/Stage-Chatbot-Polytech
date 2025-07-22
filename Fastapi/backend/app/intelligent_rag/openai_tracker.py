"""
OpenAI Token Tracking Helper
Fonctions pour tracker manuellement les vrais tokens des réponses OpenAI
"""

from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage
from color_utils import cp

def track_openai_call_manual(llm, prompt: str, operation: str, token_tracker: List[Dict[str, Any]], session_id: str) -> Dict[str, Any]:
    """
    Effectue un appel OpenAI et track les vrais tokens de la réponse
    
    Args:
        llm: L'instance LLM
        prompt: Le prompt à envoyer
        operation: Le nom de l'opération ("intent_analysis", "rag_generation", etc.)
        token_tracker: La liste pour tracker les tokens
        session_id: L'ID de session
    
    Returns:
        dict: {"response": response, "tokens": {"prompt": X, "completion": Y, "total": Z}}
    """
    
    # Effectuer l'appel OpenAI
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Extraire les vraies informations de tokens si disponibles
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    model_name = getattr(llm, 'model_name', 'gpt-4o-mini')
    
    # Essayer de récupérer les vrais tokens depuis la réponse
    if hasattr(response, 'response_metadata'):
        #cp.print_debug(f"Response metadata: {response.response_metadata}")
        token_usage = response.response_metadata.get('token_usage', {})
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        total_tokens = token_usage.get('total_tokens', 0)
    elif hasattr(response, 'usage'):
        #cp.print_debug(f"Response usage: {response.usage}")
        # Certaines versions de LangChain
        prompt_tokens = response.usage.get('prompt_tokens', 0)
        completion_tokens = response.usage.get('completion_tokens', 0)
        total_tokens = response.usage.get('total_tokens', 0)
    
    # Si on n'a pas les vrais tokens, faire une estimation simple
    if total_tokens == 0:
        cp.print_warning("⚠️ Tokens non disponibles, estimation utilisée")
        prompt_tokens = len(prompt) // 4  # Estimation grossière
        completion_tokens = len(response.content) // 4
        total_tokens = prompt_tokens + completion_tokens
    
    # Ajouter à la liste de tracking
    tracking_entry = {
        "session_id": session_id,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "model": model_name,
        "operation": operation
    }
    token_tracker.append(tracking_entry)
    
    return {
        "response": response,
        "tokens": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total_tokens,
            "model": model_name
        }
    }

def get_tokens_from_response(response) -> Dict[str, int]:
    """
    Extrait les informations de tokens d'une réponse OpenAI
    """
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    
    # Différentes façons dont les tokens peuvent être stockés
    if hasattr(response, 'response_metadata'):
        token_usage = response.response_metadata.get('token_usage', {})
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        total_tokens = token_usage.get('total_tokens', 0)
    elif hasattr(response, 'usage'):
        prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
        completion_tokens = getattr(response.usage, 'completion_tokens', 0)
        total_tokens = getattr(response.usage, 'total_tokens', 0)
    elif hasattr(response, 'token_usage'):
        prompt_tokens = response.token_usage.get('prompt_tokens', 0)
        completion_tokens = response.token_usage.get('completion_tokens', 0)
        total_tokens = response.token_usage.get('total_tokens', 0)
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    }

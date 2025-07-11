"""
Intelligent RAG System - Graph Builder
"""

import time
from langgraph.graph import StateGraph
from .state import IntelligentRAGState, IntentType
from .nodes import (
    intent_analysis_node,
    direct_answer_node,
    document_retrieval_node,
    rag_generation_node
)
from .logger import rag_logger

def create_intelligent_rag_graph():
    """
    Crée le graphe RAG intelligent avec routage basé sur l'intention
    """
    # Créer le constructeur de graphe
    builder = StateGraph(IntelligentRAGState)
    
    # Ajouter les nœuds
    builder.add_node("intent_analysis_detect", intent_analysis_node)
    builder.add_node("direct_answer", direct_answer_node)
    builder.add_node("document_retrieval", document_retrieval_node)
    builder.add_node("rag_generation", rag_generation_node)
    
    # Point d'entrée
    builder.set_entry_point("intent_analysis_detect")
    
    # Routage conditionnel basé sur l'intention
    def route_after_intent(state: IntelligentRAGState) -> str:
        """Router vers le bon nœud selon l'intention détectée"""
        intent_analysis = state.get("intent_analysis")
        
        if not intent_analysis:
            print("[Routing] Pas d'analyse d'intention, fallback vers document_retrieval")
            return "document_retrieval"  # Fallback
        
        intent = intent_analysis["intent"]
        print(f"[Routing] Intention détectée: {intent}, routage vers le bon nœud")
        
        if intent == IntentType.DIRECT_ANSWER:
            print("[Routing] → direct_answer (pas de RAG)")
            return "direct_answer"
        else:
            # Pour tous les autres types (RAG_NEEDED, SYLLABUS_*), on passe par la récupération de documents
            print("[Routing] → document_retrieval (avec RAG)")
            return "document_retrieval"
    
    # Branchement conditionnel après l'analyse d'intention
    builder.add_conditional_edges(
        "intent_analysis_detect",
        route_after_intent,
        {
            "direct_answer": "direct_answer",
            "document_retrieval": "document_retrieval"
        }
    )
    
    # Après la récupération de documents, on génère la réponse
    builder.add_edge("document_retrieval", "rag_generation")
    
    # Points de terminaison
    builder.set_finish_point("direct_answer")
    builder.set_finish_point("rag_generation")
    
    return builder.compile()

def invoke_intelligent_rag(question: str, chat_history: list = None) -> dict:
    """
    Interface principale pour utiliser le système RAG intelligent
    
    Args:
        question: La question de l'utilisateur
        chat_history: L'historique de conversation (optionnel)
    
    Returns:
        dict: Réponse avec answer, context, sources, et métadonnées
    """
    from .token_tracker import token_tracker
    import uuid
    
    initial_state = None
    start_time = time.time()
    
    # Générer un session_id unique pour tracker les coûts
    session_id = str(uuid.uuid4())
    token_tracker.start_conversation(session_id)

    try:
        # Créer le graphe
        graph = create_intelligent_rag_graph()
        
        # Préparer l'état initial - inclure le session_id pour le tracking
        initial_state = {
            "input_question": question,
            "chat_history": chat_history or [],
            "processing_steps": ["Graph initialized"],
            "session_id": session_id
        }
        
        # Exécuter le graphe
        result = graph.invoke(initial_state)
        
        # Calculer le temps de réponse
        response_time = time.time() - start_time
        
        # Finaliser le tracking des coûts
        conversation_cost = token_tracker.end_conversation(session_id)
        
        # Préparer le résultat final
        final_result = {
            "answer": result.get("answer", ""),
            "context": result.get("context", []),
            "sources": result.get("sources", []),
            "intent_analysis": result.get("intent_analysis"),
            "processing_steps": result.get("processing_steps", []),
            "error": result.get("error"),
            "success": result.get("error") is None,
            "response_time": response_time,
            "session_id": session_id,
            "token_cost": {
                "total_tokens": conversation_cost.total_tokens if conversation_cost else 0,
                "prompt_tokens": conversation_cost.total_prompt_tokens if conversation_cost else 0,
                "completion_tokens": conversation_cost.total_completion_tokens if conversation_cost else 0,
                "total_cost_usd": conversation_cost.total_cost_usd if conversation_cost else 0.0,
                "operations": [
                    {
                        "operation": op.operation,
                        "tokens": op.total_tokens,
                        "model": op.model,
                        "timestamp": op.timestamp.isoformat()
                    } for op in conversation_cost.operations
                ] if conversation_cost else []
            }
        }
        
        # Logger la conversation avec statistiques détaillées
        try:
            # Récupérer les opérations du token tracker pour cette session
            session_operations = []
            if hasattr(result, 'session_id') or 'session_id' in result:
                session_id = result.get('session_id') or getattr(result, 'session_id', None)
                if session_id:
                    from .token_tracker import token_tracker
                    session_ops = token_tracker.get_session_operations(session_id)
                    session_operations = [
                        {
                            "operation": op["operation"],
                            "model": op["model"],
                            "input_tokens": op["prompt_tokens"],
                            "output_tokens": op["completion_tokens"],
                            "cost_usd": op["cost_usd"]
                        }
                        for op in session_ops
                    ]
            
            session_id = rag_logger.log_conversation(
                question=question,
                result=final_result,
                chat_history=chat_history,
                response_time=response_time,
                intermediate_operations=session_operations
            )
            final_result["session_id"] = session_id
            print(f"[Graph] Conversation loggée: {session_id}")
        except Exception as log_error:
            print(f"[Graph] Erreur logging: {log_error}")
        
        return final_result
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"[Graph] Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        print(f"[Graph] État initial: {initial_state}")
        
        # Finaliser le tracking même en cas d'erreur
        conversation_cost = token_tracker.end_conversation(session_id)
        
        error_result = {
            "answer": "Je suis désolé, une erreur technique est survenue.",
            "context": [],
            "sources": [],
            "intent_analysis": None,
            "processing_steps": ["Critical error occurred"],
            "error": str(e),
            "success": False,
            "response_time": response_time,
            "session_id": session_id,
            "token_cost": {
                "total_tokens": conversation_cost.total_tokens if conversation_cost else 0,
                "prompt_tokens": conversation_cost.total_prompt_tokens if conversation_cost else 0,
                "completion_tokens": conversation_cost.total_completion_tokens if conversation_cost else 0,
                "total_cost_usd": conversation_cost.total_cost_usd if conversation_cost else 0.0,
                "operations": [
                    {
                        "operation": op.operation,
                        "tokens": op.total_tokens,
                        "model": op.model,
                        "timestamp": op.timestamp.isoformat()
                    } for op in conversation_cost.operations
                ] if conversation_cost else []
            }
        }
        
        # Logger l'erreur aussi
        try:
            session_id = rag_logger.log_conversation(
                question=question,
                result=error_result,
                chat_history=chat_history,
                response_time=response_time
            )
            error_result["session_id"] = session_id
        except Exception as log_error:
            print(f"[Graph] Erreur logging erreur: {log_error}")
        
        return error_result


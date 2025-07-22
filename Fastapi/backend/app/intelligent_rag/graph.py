"""
Intelligent RAG System - Graph Builder
"""

import time
import uuid
import traceback
from langgraph.graph import StateGraph
from .state import IntelligentRAGState, IntentType, INPUT_TOKEN_COST, OUTPUT_TOKEN_COST
from .state import TokenCostTrackerState
from .nodes import (
    intent_analysis_node,
    direct_answer_node,
    document_retrieval_node,
    rag_generation_node
)

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

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
            cp.print_warning("[Routing] Pas d'analyse d'intention, fallback vers document_retrieval")
            return "document_retrieval"  # Fallback
        
        intent = intent_analysis["intent"]
        cp.print_info(f"[Routing] Intention détectée: {intent}, routage vers le bon nœud")
        
        if intent == IntentType.DIRECT_ANSWER:
            cp.print_info("[Routing] → direct_answer (pas de RAG)")
            return "direct_answer"
        else:
            # Pour tous les autres types (RAG_NEEDED, SYLLABUS_*), on passe par la récupération de documents
            cp.print_info("[Routing] → document_retrieval (avec RAG)")
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

def invoke_intelligent_rag(question: str, chat_history: list = None, save_to_db: bool = True) -> dict:
    """
    Interface principale pour utiliser le système RAG intelligent
    
    Args:
        question: La question de l'utilisateur
        chat_history: L'historique de conversation (optionnel)
        save_to_db: Si True, sauvegarde dans la DB. Si False, retourne seulement les infos.
    
    Returns:
        dict: Réponse avec answer, context, sources, et métadonnées
    """
    initial_state = None
    start_time = time.time()
    
    # Générer un session_id unique pour tracker les coûts
    session_id = str(uuid.uuid4())
    
    # Créer une liste simple pour tracker les tokens
    token_tracker = []

    try:
        # Créer le graphe
        graph = create_intelligent_rag_graph()
        
        # Préparer l'état initial - inclure le session_id et token_tracker pour le tracking
        initial_state = {
            "input_question": question,
            "chat_history": chat_history or [],
            "processing_steps": ["Graph initialized"],
            "session_id": session_id,
            "token_tracker": token_tracker
        }
        
        # Exécuter le graphe
        result = graph.invoke(initial_state)
        
        # Calculer le temps de réponse
        response_time = time.time() - start_time
        
        # Calculer les statistiques des tokens depuis la liste
        total_tokens = sum(op["total_tokens"] for op in token_tracker)
        prompt_tokens = sum(op["prompt_tokens"] for op in token_tracker)
        completion_tokens = sum(op["completion_tokens"] for op in token_tracker)
        
        # Calculer le coût total
        total_cost_usd = sum(
            (op["prompt_tokens"] * INPUT_TOKEN_COST + op["completion_tokens"] * OUTPUT_TOKEN_COST) / 1000000
            for op in token_tracker
        )
        
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
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost_usd": total_cost_usd,
                "operations": token_tracker
            }
        }
        
        # Logger la conversation avec statistiques détaillées (optionnel)
        if save_to_db:
            try:
                # Les opérations sont déjà dans token_tracker
                session_operations = [
                    {
                        "operation": op["operation"],
                        "model": op["model"],
                        "input_tokens": op["prompt_tokens"],
                        "output_tokens": op["completion_tokens"],
                        "cost_usd": (op["prompt_tokens"] * INPUT_TOKEN_COST + op["completion_tokens"] * OUTPUT_TOKEN_COST) / 1000000,
                    }
                    for op in token_tracker
                ]
                
                # Pas de db_logger pour l'instant
                final_result["session_id"] = session_id
                cp.print_info(f"[Graph] Conversation loggée: {session_id}")
            except Exception as log_error:
                cp.print_error(f"[Graph] Erreur logging: {log_error}")
        else:
            # Mode sans sauvegarde - enrichir les données retournées
            try:
                # Les opérations sont déjà dans token_tracker
                session_operations = [
                    {
                        "operation": op["operation"],
                        "model": op["model"],
                        "input_tokens": op["prompt_tokens"],
                        "output_tokens": op["completion_tokens"],
                        "cost_usd": (op["prompt_tokens"] * INPUT_TOKEN_COST + op["completion_tokens"] * OUTPUT_TOKEN_COST) / 1000000,
                        "timestamp": ""  # Pas de timestamp pour l'instant
                    }
                    for op in token_tracker
                ]
                
                # Enrichir le résultat avec toutes les données détaillées
                final_result.update({
                    "detailed_operations": session_operations,
                    "conversation_metadata": {
                        "question": question,
                        "chat_history": chat_history or [],
                        "processing_time": response_time,
                        "total_context_docs": len(result.get("context", [])),
                        "total_sources": len(result.get("sources", [])),
                        "intent_confidence": result.get("intent_analysis", {}).get("confidence", 0.0) if result.get("intent_analysis") else 0.0
                    }
                })
                cp.print_info(f"[Graph] Données détaillées ajoutées (mode sans sauvegarde): {session_id}")
            except Exception as detail_error:
                cp.print_error(f"[Graph] Erreur enrichissement données: {detail_error}")
        
        return final_result
        
    except Exception as e:
        response_time = time.time() - start_time
        cp.print_error(f"[Graph] Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        cp.print_debug(f"[Graph] État initial: {initial_state}")
        
        # Calculer les statistiques même en cas d'erreur
        total_tokens = sum(op["total_tokens"] for op in token_tracker) if token_tracker else 0
        prompt_tokens = sum(op["prompt_tokens"] for op in token_tracker) if token_tracker else 0
        completion_tokens = sum(op["completion_tokens"] for op in token_tracker) if token_tracker else 0
        total_cost_usd = sum(
            (op["prompt_tokens"] * INPUT_TOKEN_COST + op["completion_tokens"] * OUTPUT_TOKEN_COST) / 1000000
            for op in token_tracker
        ) if token_tracker else 0.0
        
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
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost_usd": total_cost_usd,
                "operations": token_tracker
            }
        }
        
        # Logger l'erreur aussi (optionnel)
        if save_to_db:
            try:
                # Pas de db_logger pour l'instant
                error_result["session_id"] = session_id
                cp.print_info(f"[Graph] Erreur loggée: {session_id}")
            except Exception as log_error:
                cp.print_error(f"[Graph] Erreur logging erreur: {log_error}")
        else:
            # Mode sans sauvegarde - enrichir les données d'erreur
            try:
                session_operations = [
                    {
                        "operation": op["operation"],
                        "model": op["model"],
                        "input_tokens": op["prompt_tokens"],
                        "output_tokens": op["completion_tokens"],
                        "cost_usd": (op["prompt_tokens"] * 0.00015 + op["completion_tokens"] * 0.0006) / 1000,
                        "timestamp": ""
                    }
                    for op in token_tracker
                ]
                
                error_result.update({
                    "detailed_operations": session_operations,
                    "error_metadata": {
                        "question": question,
                        "chat_history": chat_history or [],
                        "processing_time": response_time,
                        "error_type": type(e).__name__,
                        "error_traceback": str(e)
                    }
                })
                cp.print_info(f"[Graph] Données d'erreur enrichies (mode sans sauvegarde): {session_id}")
            except Exception as detail_error:
                cp.print_error(f"[Graph] Erreur enrichissement données d'erreur: {detail_error}")
        
        return error_result
"""
Intelligent RAG System - Graph Builder
"""

import time
import uuid
import traceback
from langgraph.graph import StateGraph
from .state import IntelligentRAGState, IntentType
from .nodes import (
    intent_analysis_node,
    direct_answer_node,
    document_retrieval_node,
    rag_generation_node
)
from .db_logger import rag_db_logger

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
        
        # Logger la conversation avec statistiques détaillées (optionnel)
        if save_to_db:
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
                
                session_id = rag_db_logger.log_conversation(
                    question=question,
                    result=final_result,
                    chat_history=chat_history,
                    response_time=response_time,
                    intermediate_operations=session_operations
                )
                final_result["session_id"] = session_id
                cp.print_info(f"[Graph] Conversation loggée: {session_id}")
            except Exception as log_error:
                cp.print_error(f"[Graph] Erreur logging: {log_error}")
        else:
            # Mode sans sauvegarde - enrichir les données retournées
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
                                "cost_usd": op["cost_usd"],
                                "timestamp": op.get("timestamp", "")
                            }
                            for op in session_ops
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
        
        # Logger l'erreur aussi (optionnel)
        if save_to_db:
            try:
                session_id = rag_db_logger.log_conversation(
                    question=question,
                    result=error_result,
                    chat_history=chat_history,
                    response_time=response_time
                )
                error_result["session_id"] = session_id
                cp.print_info(f"[Graph] Erreur loggée: {session_id}")
            except Exception as log_error:
                cp.print_error(f"[Graph] Erreur logging erreur: {log_error}")
        else:
            # Mode sans sauvegarde - enrichir les données d'erreur
            try:
                from .token_tracker import token_tracker
                session_ops = token_tracker.get_session_operations(session_id)
                session_operations = [
                    {
                        "operation": op["operation"],
                        "model": op["model"],
                        "input_tokens": op["prompt_tokens"],
                        "output_tokens": op["completion_tokens"],
                        "cost_usd": op["cost_usd"],
                        "timestamp": op.get("timestamp", "")
                    }
                    for op in session_ops
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

def invoke_intelligent_rag_with_logging(question: str, chat_history: list = None) -> dict:
    """
    Interface RAG avec sauvegarde en base de données (comportement par défaut)
    
    Args:
        question: La question de l'utilisateur
        chat_history: L'historique de conversation (optionnel)
    
    Returns:
        dict: Réponse avec answer, context, sources, et métadonnées + sauvegarde DB
    """
    return invoke_intelligent_rag(question, chat_history, save_to_db=True)

def invoke_intelligent_rag_detailed(question: str, chat_history: list = None) -> dict:
    """
    Interface RAG sans sauvegarde mais avec toutes les données détaillées
    
    Args:
        question: La question de l'utilisateur
        chat_history: L'historique de conversation (optionnel)
    
    Returns:
        dict: Réponse enrichie avec toutes les données détaillées (pas de sauvegarde)
    """
    return invoke_intelligent_rag(question, chat_history, save_to_db=False)

def create_rag_conversation_from_invoke_result(invoke_result: dict) -> dict:
    """
    Adapte le résultat de invoke() pour qu'il soit compatible avec la création de RAGConversation.
    
    Args:
        invoke_result: Résultat de invoke_intelligent_rag()
        
    Returns:
        dict: Données formatées pour créer une RAGConversation
    """
    
    # Traiter l'analyse d'intention
    intent_analysis = invoke_result.get("intent_analysis")
    intent_json = None
    if intent_analysis:
        if isinstance(intent_analysis, dict):
            import json
            intent_json = json.dumps(intent_analysis)
        else:
            intent_json = str(intent_analysis)
    
    # Traiter les étapes de traitement
    processing_steps = invoke_result.get("processing_steps", [])
    processing_json = json.dumps(processing_steps) if processing_steps else None
    
    # Calculer les métriques de tokens
    token_cost = invoke_result.get("token_cost", {})
    operations = token_cost.get("operations", [])
    
    # Calculer les tokens intermédiaires à partir des opérations
    intermediate_input = 0
    intermediate_output = 0
    
    for op in operations:
        if op.get("operation") != "final_generation":  # Exclure la génération finale
            intermediate_input += op.get("input_tokens", 0)
            intermediate_output += op.get("output_tokens", 0)
    
    # Enrichir le résultat avec les données détaillées pour SQLModel
    enriched_result = {
        **invoke_result,  # Garder toutes les données originales
        "rag_conversation_data": {
            "session_id": invoke_result.get("session_id"),
            "question": invoke_result.get("question", ""),  # Sera remplacé par la vraie question
            "answer": invoke_result.get("answer", ""),
            "intent_analysis": intent_json,
            "context_docs_count": len(invoke_result.get("context", [])),
            "sources_count": len(invoke_result.get("sources", [])),
            "processing_steps": processing_json,
            "success": invoke_result.get("success", True),
            "error": invoke_result.get("error"),
            "response_time": invoke_result.get("response_time"),
            "user_input_tokens": token_cost.get("prompt_tokens", 0),
            "final_output_tokens": token_cost.get("completion_tokens", 0),
            "intermediate_input_tokens": intermediate_input,
            "intermediate_output_tokens": intermediate_output,
            "total_input_tokens": token_cost.get("prompt_tokens", 0) + intermediate_input,
            "total_output_tokens": token_cost.get("completion_tokens", 0) + intermediate_output,
            "grand_total_tokens": token_cost.get("total_tokens", 0),
            "total_cost_usd": token_cost.get("total_cost_usd", 0.0)
        },
        "token_operations_data": operations,
        "context_documents_data": invoke_result.get("context", [])
    }
    
    return enriched_result

def invoke_intelligent_rag_for_sqlmodel(question: str, chat_history: list = None, save_to_db: bool = False) -> dict:
    """
    Interface spécialisée pour retourner un résultat compatible avec SQLModel RAGConversation.
    
    Args:
        question: La question de l'utilisateur
        chat_history: L'historique de conversation (optionnel)
        save_to_db: Si True, utilise aussi l'ancien système de logging
        
    Returns:
        dict: Réponse enrichie avec les données pour SQLModel
    """
    
    # Obtenir le résultat de base
    base_result = invoke_intelligent_rag(question, chat_history, save_to_db=save_to_db)
    
    # Enrichir avec les données SQLModel
    enriched_result = create_rag_conversation_from_invoke_result(base_result)
    
    # Ajouter la question originale
    enriched_result["rag_conversation_data"]["question"] = question
    
    return enriched_result

# def invoke_intelligent_rag(question: str, chat_history: list = None) -> dict:
#     """
#     Interface principale pour utiliser le système RAG intelligent
    
#     Args:
#         question: La question de l'utilisateur
#         chat_history: L'historique de conversation (optionnel)
    
#     Returns:
#         dict: Réponse avec answer, context, sources, et métadonnées
#     """
#     from .token_tracker import token_tracker
#     import uuid
    
#     initial_state = None
#     start_time = time.time()
    
#     # Générer un session_id unique pour tracker les coûts
#     session_id = str(uuid.uuid4())
#     token_tracker.start_conversation(session_id)

#     try:
#         # Créer le graphe
#         graph = create_intelligent_rag_graph()
        
#         # Préparer l'état initial - inclure le session_id pour le tracking
#         initial_state = {
#             "input_question": question,
#             "chat_history": chat_history or [],
#             "processing_steps": ["Graph initialized"],
#             "session_id": session_id
#         }
        
#         # Exécuter le graphe
#         result = graph.invoke(initial_state)
        
#         # Calculer le temps de réponse
#         response_time = time.time() - start_time
        
#         # Finaliser le tracking des coûts
#         conversation_cost = token_tracker.end_conversation(session_id)
        
#         # Préparer le résultat final
#         final_result = {
#             "answer": result.get("answer", ""),
#             "context": result.get("context", []),
#             "sources": result.get("sources", []),
#             "intent_analysis": result.get("intent_analysis"),
#             "processing_steps": result.get("processing_steps", []),
#             "error": result.get("error"),
#             "success": result.get("error") is None,
#             "response_time": response_time,
#             "session_id": session_id,
#             "token_cost": {
#                 "total_tokens": conversation_cost.total_tokens if conversation_cost else 0,
#                 "prompt_tokens": conversation_cost.total_prompt_tokens if conversation_cost else 0,
#                 "completion_tokens": conversation_cost.total_completion_tokens if conversation_cost else 0,
#                 "total_cost_usd": conversation_cost.total_cost_usd if conversation_cost else 0.0,
#                 "operations": [
#                     {
#                         "operation": op.operation,
#                         "tokens": op.total_tokens,
#                         "model": op.model,
#                         "timestamp": op.timestamp.isoformat()
#                     } for op in conversation_cost.operations
#                 ] if conversation_cost else []
#             }
#         }
        
#         # Logger la conversation avec statistiques détaillées
#         try:
#             # Récupérer les opérations du token tracker pour cette session
#             session_operations = []
#             if hasattr(result, 'session_id') or 'session_id' in result:
#                 session_id = result.get('session_id') or getattr(result, 'session_id', None)
#                 if session_id:
#                     from .token_tracker import token_tracker
#                     session_ops = token_tracker.get_session_operations(session_id)
#                     session_operations = [
#                         {
#                             "operation": op["operation"],
#                             "model": op["model"],
#                             "input_tokens": op["prompt_tokens"],
#                             "output_tokens": op["completion_tokens"],
#                             "cost_usd": op["cost_usd"]
#                         }
#                         for op in session_ops
#                     ]
            
#             session_id = rag_db_logger.log_conversation(
#                 question=question,
#                 result=final_result,
#                 chat_history=chat_history,
#                 response_time=response_time,
#                 intermediate_operations=session_operations
#             )
#             final_result["session_id"] = session_id
#             cp.print_info(f"[Graph] Conversation loggée: {session_id}")
#         except Exception as log_error:
#             cp.print_error(f"[Graph] Erreur logging: {log_error}")
        
#         return final_result
        
#     except Exception as e:
#         response_time = time.time() - start_time
#         cp.print_error(f"[Graph] Erreur critique: {e}")
#         import traceback
#         traceback.print_exc()
#         cp.print_debug(f"[Graph] État initial: {initial_state}")
        
#         # Finaliser le tracking même en cas d'erreur
#         conversation_cost = token_tracker.end_conversation(session_id)
        
#         error_result = {
#             "answer": "Je suis désolé, une erreur technique est survenue.",
#             "context": [],
#             "sources": [],
#             "intent_analysis": None,
#             "processing_steps": ["Critical error occurred"],
#             "error": str(e),
#             "success": False,
#             "response_time": response_time,
#             "session_id": session_id,
#             "token_cost": {
#                 "total_tokens": conversation_cost.total_tokens if conversation_cost else 0,
#                 "prompt_tokens": conversation_cost.total_prompt_tokens if conversation_cost else 0,
#                 "completion_tokens": conversation_cost.total_completion_tokens if conversation_cost else 0,
#                 "total_cost_usd": conversation_cost.total_cost_usd if conversation_cost else 0.0,
#                 "operations": [
#                     {
#                         "operation": op.operation,
#                         "tokens": op.total_tokens,
#                         "model": op.model,
#                         "timestamp": op.timestamp.isoformat()
#                     } for op in conversation_cost.operations
#                 ] if conversation_cost else []
#             }
#         }
        
#         # Logger l'erreur aussi
#         try:
#             session_id = rag_db_logger.log_conversation(
#                 question=question,
#                 result=error_result,
#                 chat_history=chat_history,
#                 response_time=response_time
#             )
#             error_result["session_id"] = session_id
#         except Exception as log_error:
#             cp.print_error(f"[Graph] Erreur logging erreur: {log_error}")
        
#         return error_result
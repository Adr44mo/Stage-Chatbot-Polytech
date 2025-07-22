from .models import Conversation, Message, RAGConversation, RAGTokenOperation, RAGContextDocument
from fastapi import Depends, HTTPException, status, Cookie
from sqlmodel import Session, select
from ..database.database import get_session, engine
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from color_utils import cp

def update_rag_conversation(
    invoke_result: Dict[str, Any], 
    conversation: Conversation,
    session: Session = Depends(get_session)
) -> RAGConversation:
    """
    Créer une instance RAGConversation à partir du résultat de invoke() et d'une conversation.
    
    Args:
        invoke_result: Résultat de invoke_intelligent_rag()
        conversation: Instance de Conversation existante
        session: Session de base de données
        
    Returns:
        RAGConversation: Instance créée et sauvegardée
    """
    
    # Récupérer les messages de la conversation pour avoir la question
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.timestamp.desc())
    ).all()
    
    # Trouver la dernière question de l'utilisateur
    last_user_question = None
    for message in messages:
        if message.role == "user":
            last_user_question = message.content
            break
    
    cp.print_debug(f"Last user question found: {last_user_question}")
    cp.print_debug(f"Invoke result: {invoke_result.get('question', 'Question non trouvée')}")
    # Si pas de question trouvée, utiliser celle du résultat ou une valeur par défaut
    question = last_user_question or invoke_result.get("question", "Question non trouvée")
    
    # Extraire les données des tokens
    token_cost = invoke_result.get("token_cost", {})
    
    # Créer l'instance RAGConversation
    rag_conversation = RAGConversation(
        session_id=invoke_result.get("session_id", conversation.session_id),
        timestamp=datetime.utcnow(),
        conversation_id=conversation.id,
        question=question,
        answer=invoke_result.get("answer", ""),
        intent_analysis=json.dumps(invoke_result.get("intent_analysis")) if invoke_result.get("intent_analysis") else None,
        context_docs_count=len(invoke_result.get("context", [])),
        sources_count=len(invoke_result.get("sources", [])),
        processing_steps=json.dumps(invoke_result.get("processing_steps", [])),
        success=invoke_result.get("success", True),
        error=invoke_result.get("error"),
        response_time=invoke_result.get("response_time"),
        user_input_tokens=token_cost.get("prompt_tokens", 0),
        final_output_tokens=token_cost.get("completion_tokens", 0),
        intermediate_input_tokens=0,  # Peut être calculé à partir des opérations
        intermediate_output_tokens=0,  # Peut être calculé à partir des opérations
        total_input_tokens=token_cost.get("prompt_tokens", 0),
        total_output_tokens=token_cost.get("completion_tokens", 0),
        grand_total_tokens=token_cost.get("total_tokens", 0),
        total_cost_usd=token_cost.get("total_cost_usd", 0.0)
    )
    
    # Sauvegarder la conversation RAG
    session.add(rag_conversation)
    session.commit()
    session.refresh(rag_conversation)
    
    # Créer les opérations de tokens si elles existent
    operations = invoke_result.get("token_cost", {}).get("operations", [])
    if hasattr(invoke_result, 'detailed_operations'):
        operations = invoke_result.get("detailed_operations", [])
    
    for operation in operations:
        token_operation = RAGTokenOperation(
            rag_conversation_id=rag_conversation.id,
            session_id=rag_conversation.session_id,
            operation=operation.get("operation", "unknown"),
            model=operation.get("model", "unknown"),
            input_tokens=operation.get("prompt_tokens", 0),
            output_tokens=operation.get("completion_tokens", 0),
            total_tokens=operation.get("tokens", operation.get("total_tokens", 0)),
            cost_usd=operation.get("cost_usd", 0.0),
            timestamp=datetime.fromisoformat(operation.get("timestamp", datetime.utcnow().isoformat()).replace('Z', '+00:00')) if operation.get("timestamp") else datetime.utcnow()
        )
        session.add(token_operation)
    
    # Créer les documents contextuels si ils existent
    context_docs = invoke_result.get("context", [])
    for i, doc in enumerate(context_docs):
        # Si c'est un dictionnaire avec des métadonnées
        if isinstance(doc, dict):
            content_preview = doc.get("content", doc.get("page_content", str(doc)))[:500]
            metadata = json.dumps(doc.get("metadata", {}))
        else:
            # Si c'est juste du texte
            content_preview = str(doc)[:500]
            metadata = json.dumps({"index": i})
        
        context_document = RAGContextDocument(
            rag_conversation_id=rag_conversation.id,
            session_id=rag_conversation.session_id,
            content_preview=content_preview,
            metadonnee=metadata
        )
        session.add(context_document)
    
    # Commit final pour les relations
    session.commit()
    
    return rag_conversation
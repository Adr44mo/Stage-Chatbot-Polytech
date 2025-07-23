"""
Intelligent RAG System - Core Nodes
"""

import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage
from ..llmm import llm, db, initialize_the_rag_chain
from ..chat import get_sources
from .state import IntelligentRAGState, IntentType, SpecialityType, IntentAnalysisResult
from .openai_tracker import track_openai_call_manual, get_tokens_from_response
from .prompts import (
    get_intent_analysis_prompt,
    get_direct_answer_prompt,
    get_general_rag_prompt,
    get_speciality_overview_prompt
)
from color_utils import ColorPrint as cp

def intent_analysis_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Analyse l'intention de l'utilisateur en utilisant OpenAI avec sortie JSON
    """
    cp.print_step("Analyse d'intention")
    cp.print_info(f"État reçu: {list(state.keys())}")
    
    try:
        # Récupérer la liste token tracker du state
        token_tracker = state.get("token_tracker", [])
        session_id = state.get("session_id", "unknown")
        
        # Construire l'historique de conversation (seulement les 5 derniers messages)
        history_text = ""
        if state.get("chat_history"):
            last_msgs = state["chat_history"][-6:]
            history_text = "\n".join([
            f"User: {msg['content']}" if msg['role'] == "user" else f"Assistant: {msg['content']}"
            for msg in last_msgs
            ])
        
        # Prompt structuré pour obtenir une réponse JSON
        prompt = get_intent_analysis_prompt(state['input_question'], history_text)

        # Utiliser le tracking manuel pour récupérer les vrais tokens
        track_result = track_openai_call_manual(
            llm=llm, 
            prompt=prompt, 
            operation="intent_analysis", 
            token_tracker=token_tracker, 
            session_id=session_id
        )
        response = track_result["response"]
        token_info = track_result["tokens"]
        cp.print_info(f"Tokens utilisés: {token_info['total']} (prompt: {token_info['prompt']}, completion: {token_info['completion']})")
        
        # Parser la réponse JSON
        try:
            # Nettoyer la réponse en supprimant les balises markdown
            clean_response = response.content.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]  # Supprimer ```json
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]  # Supprimer ```
            clean_response = clean_response.strip()
            
            result = json.loads(clean_response)
            
            # Validation et conversion
            intent_analysis = IntentAnalysisResult(
                intent=IntentType(result["intent"]),
                speciality=SpecialityType(result["speciality"]) if result.get("speciality") and result["speciality"] != "null" else None,
                confidence=float(result.get("confidence", 0.8)),
                reasoning=result.get("reasoning", ""),
                needs_history=result.get("needs_history", False),
                course_name=result.get("course_name") if result.get("course_name") and result["course_name"] != "null" else None,
                reformulation=result.get("reformulation") if result.get("reformulation") and result["reformulation"] != "null" else None
            )
            cp.print_debug(f"raw: {result}")
            
            cp.print_success(f"Intention détectée: {intent_analysis['intent']}")
            cp.print_info(f"Spécialité: {intent_analysis['speciality']}")
            cp.print_info(f"Confiance: {intent_analysis['confidence']:.2f}")
            
            return {
                "intent_analysis": intent_analysis,
                "processing_steps": state.get("processing_steps", []) + ["Intent analysis completed"]
            }
            
        except json.JSONDecodeError as e:
            cp.print_error(f"Erreur parsing JSON: {e}")
            cp.print_warning(f"Réponse brute: {response.content}")
            
            # Fallback avec classification simple
            content = response.content.lower()
            if any(word in content for word in ["direct", "greeting", "casual"]):
                intent = IntentType.DIRECT_ANSWER
            elif any(word in content for word in ["syllabus", "toc"]):
                intent = IntentType.SYLLABUS_SPECIALITY_OVERVIEW
            else:
                intent = IntentType.RAG_NEEDED
            
            fallback_analysis = IntentAnalysisResult(
                intent=intent,
                speciality=None,
                confidence=0.5,
                reasoning="Fallback classification due to JSON parsing error",
                needs_history=False,
                course_name=None
            )
            
            cp.print_warning("Utilisation du fallback pour l'analyse d'intention")
            
            return {
                "intent_analysis": fallback_analysis,
                "processing_steps": state.get("processing_steps", []) + ["Intent analysis with fallback"]
            }
            
    except Exception as e:
        cp.print_error(f"Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        return {
            "intent_analysis": IntentAnalysisResult(
                intent=IntentType.RAG_NEEDED,
                speciality=None,
                confidence=0.3,
                reasoning=f"Error in analysis: {str(e)}",
                needs_history=False,
                course_name=None
            ),
            "processing_steps": state.get("processing_steps", []) + ["Intent analysis failed"],
            "error": str(e)
        }

def direct_answer_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Génère une réponse directe sans recherche documentaire
    """
    cp.print_step("Génération de réponse directe")
    
    try:
        # Récupérer la liste token tracker du state
        token_tracker = state.get("token_tracker", [])
        session_id = state.get("session_id", "unknown")
        
        prompt = get_direct_answer_prompt(state['input_question'])

        # Utiliser le tracking manuel pour récupérer les vrais tokens
        track_result = track_openai_call_manual(
            llm=llm, 
            prompt=prompt, 
            operation="direct_answer", 
            token_tracker=token_tracker, 
            session_id=session_id
        )
        response = track_result["response"]
        token_info = track_result["tokens"]
        cp.print_info(f"Tokens utilisés: {token_info['total']} (prompt: {token_info['prompt']}, completion: {token_info['completion']})")
            
        answer = response.content.strip()
        
        cp.print_success("Réponse directe générée")
        
        return {
            "answer": answer,
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["Direct answer generated"]
        }
        
    except Exception as e:
        cp.print_error(f"Erreur: {e}")
        return {
            "answer": "Je suis désolé, je rencontre une difficulté technique. Pouvez-vous reformuler votre question ?",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["Direct answer failed"],
            "error": str(e)
        }

def document_retrieval_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Récupère les documents pertinents selon l'intention
    """
    try:
        intent_analysis = state.get("intent_analysis")
        if not intent_analysis:
            raise ValueError("Intent analysis not found")
        
        cp.print_step(f"Récupération pour intention: {intent_analysis['intent']}")
        
        # Traitement unifié : seules les vues d'ensemble de spécialité ont un traitement spécial
        if intent_analysis["intent"] == IntentType.SYLLABUS_SPECIALITY_OVERVIEW and not intent_analysis["speciality"] == "GENERAL":
            docs = _retrieve_speciality_overview_docs(state)
        else:
            # Traitement classique pour RAG_NEEDED et SYLLABUS_SPECIFIC_COURSE
            docs = _retrieve_general_docs(state)
        
        cp.print_success(f"{len(docs)} documents récupérés")
        
        return {
            "retrieved_docs": docs,
            "processing_steps": state.get("processing_steps", []) + ["Documents retrieved"]
        }
        
    except Exception as e:
        cp.print_error(f"Erreur: {e}")
        return {
            "retrieved_docs": [],
            "processing_steps": state.get("processing_steps", []) + ["Document retrieval failed"],
            "error": str(e)
        }

def _retrieve_speciality_overview_docs(state: IntelligentRAGState) -> List[Any]:
    """Récupération spécialisée pour une vue d'ensemble des cours d'une spécialité"""
    intent_analysis = state["intent_analysis"]
    question = state["input_question"]
    speciality = intent_analysis.get("speciality")
    
    try:
        # Recherche directe par métadonnées pour les documents TOC
        cp.print_info(f"[Retrieval] Recherche TOC pour spécialité: {speciality}")
        
        # Récupérer TOUS les documents de la collection
        collection = db.get()
        all_docs = []
        
        # Reconstruire les documents avec leurs métadonnées
        for i, doc_id in enumerate(collection['ids']):
            metadata = collection['metadatas'][i]
            content = collection['documents'][i]
            
            # Créer un objet Document-like
            doc_obj = type('Document', (), {
                'page_content': content,
                'metadata': metadata
            })()
            all_docs.append(doc_obj)
        
        # Filtrer pour les documents TOC de la spécialité avec critères précis
        filtered_docs = []
        speciality_name = speciality.value if speciality else None
        
        for doc in all_docs:
            metadata = doc.metadata
            
            # 1. CRITÈRE PRINCIPAL : metadata.type doit être "toc"
            metadata_type = str(metadata.get("metadata.type", "")).lower()
            is_toc_doc = (metadata_type == "toc")
            
            # 2. CRITÈRE SPÉCIALITÉ : metadata.specialite doit correspondre
            metadata_specialite = str(metadata.get("metadata.specialite", "")).upper()
            speciality_match = True
            
            if speciality_name and speciality_name != "GENERAL":
                # Correspondance exacte avec la spécialité
                speciality_match = (metadata_specialite == speciality_name)
            
            # Les DEUX critères doivent être vrais
            if is_toc_doc and speciality_match:
                filtered_docs.append(doc)
                cp.print_info(f"[Retrieval] TOC trouvé: type={metadata_type}, specialite={metadata_specialite}")
        
        # Si pas assez de documents TOC, faire une recherche complémentaire
        if len(filtered_docs) < 2:
            cp.print_warning(f"[Retrieval] Seulement {len(filtered_docs)} docs TOC trouvés, recherche complémentaire...")
            
            # Recherche par similarité comme backup MAIS toujours avec les critères TOC
            similarity_docs = db.similarity_search(question, k=15)
            
            for doc in similarity_docs:
                if doc not in filtered_docs:
                    metadata = doc.metadata
                    
                    # Vérifier TOUJOURS les critères TOC stricts
                    metadata_type = str(metadata.get("metadata.type", "")).lower()
                    metadata_specialite = str(metadata.get("metadata.specialite", "")).upper()
                    
                    is_toc_doc = (metadata_type == "toc")
                    speciality_match = True
                    
                    if speciality_name and speciality_name != "GENERAL":
                        speciality_match = (metadata_specialite == speciality_name)
                    
                    if is_toc_doc and speciality_match:
                        filtered_docs.append(doc)
                        cp.print_info(f"[Retrieval] TOC complémentaire: type={metadata_type}, specialite={metadata_specialite}")
        
        cp.print_success(f"[Retrieval] {len(filtered_docs)} documents TOC récupérés au total")
        return filtered_docs[:12]  # Garder plus de documents pour une vue d'ensemble complète
        
    except Exception as e:
        cp.print_error(f"[Retrieval] Erreur récupération vue d'ensemble spécialité: {e}")
        import traceback
        traceback.print_exc()
        return []

def _filter_by_speciality(docs: List[Any], speciality: SpecialityType) -> List[Any]:
    """Filtre les documents par spécialité"""
    if not speciality:
        return docs
    
    # Mots-clés par spécialité pour filtrage
    speciality_keywords = {
        SpecialityType.MAIN: ["main", "mathématiques appliquées", "informatique"],
        SpecialityType.AGRAL: ["agral", "agroalimentaire"],
        SpecialityType.EISE: ["eise", "électronique", "systèmes embarqués"],
        SpecialityType.EI2I: ["ei2i", "électronique", "informatique industrielle"],
        SpecialityType.GM: ["gm", "génie mécanique", "mécanique"],
        SpecialityType.MTX: ["mtx", "matériaux"],
        SpecialityType.ROB: ["rob", "robotique"],
        SpecialityType.ST: ["st", "sciences de la terre", "géologie"]
    }
    
    if speciality not in speciality_keywords:
        return docs
    
    keywords = speciality_keywords[speciality]
    filtered_docs = []
    
    for doc in docs:
        metadata = doc.metadata
        tags = str(metadata.get("tags", "")).lower()
        title = str(metadata.get("metadata.title", "")).lower()
        specialite = str(metadata.get("metadata.specialite", "")).lower()
        
        # Vérifier la correspondance de spécialité
        speciality_match = any(
            keyword in text for text in [tags, title, specialite]
            for keyword in keywords
        )
        
        if speciality_match:
            filtered_docs.append(doc)
    
    return filtered_docs

def rag_generation_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Génère une réponse en utilisant les documents récupérés
    """
    try:
        intent_analysis = state.get("intent_analysis")
        retrieved_docs = state.get("retrieved_docs", [])
        
        if not retrieved_docs:
            # Fallback vers RAG standard
            cp.print_warning("[RAG] Pas de documents, utilisation RAG standard")
            return _fallback_rag_generation(state)
        
        # Génération simplifiée : seules les vues d'ensemble de spécialité ont un traitement spécial
        if intent_analysis and intent_analysis["intent"] == IntentType.SYLLABUS_SPECIALITY_OVERVIEW:
            return _generate_speciality_overview_response(state, retrieved_docs)
        else:
            # Traitement unifié pour RAG_NEEDED et SYLLABUS_SPECIFIC_COURSE
            return _generate_general_response(state, retrieved_docs)
            
    except Exception as e:
        cp.print_error(f"[RAG] Erreur: {e}")
        return {
            "answer": "Je suis désolé, je rencontre une difficulté pour traiter votre demande.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["RAG generation failed"],
            "error": str(e)
        }

def _generate_general_response(state: IntelligentRAGState, docs: List[Any]) -> Dict[str, Any]:
    """Génère une réponse générale (pour RAG_NEEDED et SYLLABUS_SPECIFIC_COURSE)"""
    
    if not docs:
        return {
            "answer": "Je n'ai pas trouvé d'informations correspondant à votre question dans ma base de données.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["No general documents found"]
        }
    
    context_text = "\n\n".join([doc.page_content for doc in docs[:6]])
    
    # Utiliser l'historique si nécessaire
    intent_analysis = state.get("intent_analysis")
    history_context = ""
    if intent_analysis and intent_analysis.get("needs_history") and state.get("chat_history"):
        history_context = "\n".join([
            f"User: {msg['content']}" if msg['role'] == "user" else f"Assistant: {msg['content']}"
            for msg in state["chat_history"]
        ])
        history_context = f"\n\nHistorique de conversation:\n{history_context}\n"

    # Utiliser la reformulation si disponible
    reformulated_question = state.get("intent_analysis", {}).get("reformulation")
    if reformulated_question:
        question = reformulated_question
    else:
        question = state["input_question"]

    prompt = get_general_rag_prompt(
        input_question=question,
        context_text=context_text,
        history_context=history_context
    )

    # Récupérer la liste token tracker du state
    token_tracker = state.get("token_tracker", [])
    session_id = state.get("session_id", "unknown")
    
    # Utiliser le tracking manuel pour récupérer les vrais tokens
    track_result = track_openai_call_manual(
        llm=llm, 
        prompt=prompt, 
        operation="rag_generation_general", 
        token_tracker=token_tracker, 
        session_id=session_id
    )
    response = track_result["response"]
    token_info = track_result["tokens"]
    cp.print_info(f"Tokens utilisés: {token_info['total']} (prompt: {token_info['prompt']}, completion: {token_info['completion']})")
        
    answer = response.content.strip()
    
    # Extraire les sources
    sources = get_sources(docs) if docs else []
    
    cp.print_success(f"[RAG] Réponse générale générée avec {len(docs)} documents")
    
    return {
        "answer": answer,
        "context": docs,
        "sources": sources,
        "processing_steps": state.get("processing_steps", []) + ["General response generated"]
    }

def _generate_speciality_overview_response(state: IntelligentRAGState, docs: List[Any]) -> Dict[str, Any]:
    """Génère une réponse spécialisée pour une vue d'ensemble des cours d'une spécialité"""
    intent_analysis = state.get("intent_analysis")
    speciality = intent_analysis.get("speciality") if intent_analysis else None
    
    if not docs:
        speciality_name = speciality.value if speciality else "la spécialité demandée"
        return {
            "answer": f"Je n'ai pas trouvé d'informations sur les cours de {speciality_name}.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["No speciality overview documents found"]
        }
    
    context_text = "\n\n".join([doc.page_content for doc in docs[:8]])
    
    # Utiliser l'historique si nécessaire
    history_context = ""
    if intent_analysis and intent_analysis.get("needs_history") and state.get("chat_history"):
        history_context = "\n".join([
            f"User: {msg['content']}" if msg['role'] == "user" else f"Assistant: {msg['content']}"
            for msg in state["chat_history"]
        ])
        history_context = f"\n\nHistorique de conversation:\n{history_context}\n"
    
    speciality_name = speciality.value if speciality else "la spécialité"
    
    prompt = get_speciality_overview_prompt(
        input_question=state['input_question'],
        context_text=context_text,
        speciality_name=speciality_name,
        history_context=history_context
    )

    # Récupérer la liste token tracker du state
    token_tracker = state.get("token_tracker", [])
    session_id = state.get("session_id", "unknown")
    
    # Utiliser le tracking manuel pour récupérer les vrais tokens
    track_result = track_openai_call_manual(
        llm=llm, 
        prompt=prompt, 
        operation="rag_generation_speciality", 
        token_tracker=token_tracker, 
        session_id=session_id
    )
    response = track_result["response"]
    token_info = track_result["tokens"]
    cp.print_info(f"Tokens utilisés: {token_info['total']} (prompt: {token_info['prompt']}, completion: {token_info['completion']})")
        
    answer = response.content.strip()
    
    # Extraire les sources
    sources = get_sources(docs) if docs else []
    
    cp.print_success(f"[RAG] Réponse vue d'ensemble spécialité générée avec {len(docs)} documents")
    
    return {
        "answer": answer,
        "context": docs,
        "sources": sources,
        "processing_steps": state.get("processing_steps", []) + ["speciality overview response generated"]
    }

def _fallback_rag_generation(state: IntelligentRAGState) -> Dict[str, Any]:
    """Génération RAG de secours"""
    try:
        rag_chain = initialize_the_rag_chain()
        response = rag_chain.invoke({
            "input": state["input_question"],
            "chat_history": state.get("chat_history", [])
        })
        
        context_docs = response.get("context", [])
        sources = get_sources(context_docs) if context_docs else []
        
        return {
            "answer": response.get("answer", ""),
            "context": context_docs,
            "sources": sources,
            "processing_steps": state.get("processing_steps", []) + ["Fallback RAG used"]
        }
        
    except Exception as e:
        cp.print_error(f"[RAG] Erreur fallback: {e}")
        return {
            "answer": "Je suis désolé, je ne peux pas traiter votre demande pour le moment.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["Fallback RAG failed"],
            "error": str(e)
        }

def _retrieve_general_docs(state: IntelligentRAGState) -> List[Any]:
    """Récupération classique pour les documents généraux (RAG standard)"""
    reformulated_question = state.get("intent_analysis", {}).get("reformulation")
    if reformulated_question:
        question = reformulated_question
    else:
        question = state["input_question"]
    
    try:
        # Recherche standard avec similarité
        docs = db.similarity_search(question, k=12)
        return docs[:8]  # Garder les 8 meilleurs documents
        
    except Exception as e:
        cp.print_error(f"[Retrieval] Erreur récupération générale: {e}")
        return []

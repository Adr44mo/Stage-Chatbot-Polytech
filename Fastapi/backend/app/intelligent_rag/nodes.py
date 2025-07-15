"""
Intelligent RAG System - Core Nodes
"""

import json
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage
from ..llmm import llm, db, initialize_the_rag_chain
from ..chat import get_sources
from .state import IntelligentRAGState, IntentType, SpecialityType, IntentAnalysisResult
from .token_tracker import track_openai_call, token_tracker

@track_openai_call("intent_analysis")
def intent_analysis_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Analyse l'intention de l'utilisateur en utilisant OpenAI avec sortie JSON
    """
    print(f"[Intent] Début - État reçu: {list(state.keys())}")
    print(f"[Intent] État complet: {state}")
    
    try:
        # Construire l'historique de conversation
        history_text = ""
        if state.get("chat_history"):
            history_text = "\n".join([
                f"User: {msg['content']}" if msg['role'] == "user" else f"Assistant: {msg['content']}"
                for msg in state["chat_history"]
            ])
        
        # Prompt structuré pour obtenir une réponse JSON
        prompt = f"""You are an intent classification system for Polytech Sorbonne chatbot.
Analyze the user's question and return a JSON response with this exact structure:

{{
    "intent": "DIRECT_ANSWER|RAG_NEEDED|SYLLABUS_SPECIFIC_COURSE|SYLLABUS_SPECIALITY_OVERVIEW",
    "speciality": "AGRAL|EISE|EI2I|GM|MAIN|MTX|ROB|ST|GENERAL|null",
    "confidence": 0.95,
    "reasoning": "Brief explanation of the classification",
    "needs_history": true,
    "course_name": "Course name if specific course mentioned, otherwise null"
}}

Classification rules:
- DIRECT_ANSWER: Only for greetings, thanks, casual conversation unrelated to Polytech
- RAG_NEEDED: For factual questions about Polytech (admissions, campus, associations, testimonials, general information about the speciality, etc.)
- SYLLABUS_SPECIFIC_COURSE: For questions about a specific course (e.g., "What is taught in Algorithmique?")
- SYLLABUS_SPECIALITY_OVERVIEW: For questions about all courses of a speciality or general curriculum (e.g., "What courses are in ROB speciality?", "Table of contents")

Specialities:
- AGRAL: Agroalimentaire
- EISE: Électronique et Informatique - Systèmes Embarqués
- EI2I: Électronique et Informatique - Informatique Industrielle
- GM: Génie Mécanique
- MAIN: Mathématiques Appliquées et Informatique
- MTX: Matériaux
- ROB: Robotique
- ST: Sciences de la Terre
- GENERAL: General curriculum questions without specific speciality

History necessity rules:
- needs_history: true if the question refers to "this", "that", previous conversation, or context is needed
- needs_history: false if the question is self-contained

Context:
{history_text}

Question: {state['input_question']}

Return only valid JSON:"""

        response = llm.invoke([HumanMessage(content=prompt)])
        
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
                course_name=result.get("course_name") if result.get("course_name") and result["course_name"] != "null" else None
            )
            
            print(f"[Intent] Intention détectée: {intent_analysis['intent']}")
            print(f"[Intent] Spécialité: {intent_analysis['speciality']}")
            print(f"[Intent] Confiance: {intent_analysis['confidence']}")
            
            return {
                "intent_analysis": intent_analysis,
                "processing_steps": state.get("processing_steps", []) + ["Intent analysis completed"]
            }
            
        except json.JSONDecodeError as e:
            print(f"[Intent] Erreur parsing JSON: {e}")
            print(f"[Intent] Réponse brute: {response.content}")
            
            # Fallback avec classification simple
            content = response.content.lower()
            if any(word in content for word in ["direct", "greeting", "casual"]):
                intent = IntentType.DIRECT_ANSWER
            elif any(word in content for word in ["syllabus", "toc", "course"]):
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
            
            return {
                "intent_analysis": fallback_analysis,
                "processing_steps": state.get("processing_steps", []) + ["Intent analysis with fallback"]
            }
            
    except Exception as e:
        print(f"[Intent] Erreur lors de l'analyse: {e}")
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

@track_openai_call("direct_answer")
def direct_answer_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Génère une réponse directe sans recherche documentaire
    """
    try:
        direct_prompt = f"""Tu es l'assistant virtuel de Polytech Sorbonne. Tu réponds aux salutations et questions générales.

Règles:
- Reste professionnel et amical
- Pour les salutations, présente-toi brièvement
- Pour les questions générales, propose d'aider avec des informations spécifiques sur Polytech
- Réponds dans la langue de la question

Question: {state['input_question']}

Réponse:"""

        response = llm.invoke([HumanMessage(content=direct_prompt)])
        answer = response.content.strip()
        
        print(f"[Direct] Réponse directe générée")
        
        return {
            "answer": answer,
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["Direct answer generated"]
        }
        
    except Exception as e:
        print(f"[Direct] Erreur: {e}")
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
        
        print(f"[Retrieval] Récupération pour intention: {intent_analysis['intent']}")
        
        # Différentes stratégies selon l'intention
        if intent_analysis["intent"] == IntentType.SYLLABUS_SPECIALITY_OVERVIEW:
            docs = _retrieve_speciality_overview_docs(state)
        elif intent_analysis["intent"] == IntentType.SYLLABUS_SPECIFIC_COURSE:
            docs = _retrieve_specific_course_docs(state)
        else:
            docs = _retrieve_general_docs(state)
        
        print(f"[Retrieval] {len(docs)} documents récupérés")
        
        return {
            "retrieved_docs": docs,
            "processing_steps": state.get("processing_steps", []) + ["Documents retrieved"]
        }
        
    except Exception as e:
        print(f"[Retrieval] Erreur: {e}")
        return {
            "retrieved_docs": [],
            "processing_steps": state.get("processing_steps", []) + ["Document retrieval failed"],
            "error": str(e)
        }

def _retrieve_specific_course_docs(state: IntelligentRAGState) -> List[Any]:
    """Récupération spécialisée pour un cours spécifique"""
    intent_analysis = state["intent_analysis"]
    question = state["input_question"]
    course_name = intent_analysis.get("course_name")
    
    try:
        # Construire la requête avec le nom du cours si disponible
        search_query = question
        if course_name:
            search_query = f"{course_name} {question}"
        
        # Recherche avec plus de documents pour pouvoir filtrer
        docs = db.similarity_search(search_query, k=20)
        
        # Filtrer pour garder SEULEMENT les documents syllabus/cours
        filtered_docs = []
        for doc in docs:
            metadata = doc.metadata
            tags = str(metadata.get("tags", "")).lower()
            doc_type = str(metadata.get("metadata.type", "")).lower()
            document_type = str(metadata.get("document_type", "")).lower()
            content = str(doc.page_content).lower()
            
            # INCLURE les documents de cours spécifiques
            is_course_doc = (
                # Tags contiennent "cours" ou "syllabus"
                "cours" in tags or "syllabus" in tags or
                # Type est fiche_cours
                doc_type == "fiche_cours" or
                # Document type cours
                document_type == "cours"
            )
            
            # Si un nom de cours est spécifié, vérifier la correspondance
            if course_name and is_course_doc:
                course_match = (
                    course_name.lower() in content or
                    course_name.lower() in tags or
                    any(word in content for word in course_name.lower().split())
                )
                if course_match:
                    filtered_docs.append(doc)
            elif not course_name and is_course_doc:
                filtered_docs.append(doc)
        
        # Optionnel : filtrer par spécialité si spécifiée
        speciality = intent_analysis.get("speciality")
        if speciality and filtered_docs:
            speciality_filtered_docs = _filter_by_speciality(filtered_docs, speciality)
            if len(speciality_filtered_docs) >= 2:
                filtered_docs = speciality_filtered_docs
        
        print(f"[Retrieval] {len(filtered_docs)} documents de cours spécifique récupérés")
        return filtered_docs[:8]  # Garder les 8 meilleurs
        
    except Exception as e:
        print(f"[Retrieval] Erreur récupération cours spécifique: {e}")
        return []

def _retrieve_speciality_overview_docs(state: IntelligentRAGState) -> List[Any]:
    """Récupération spécialisée pour une vue d'ensemble des cours d'une spécialité"""
    intent_analysis = state["intent_analysis"]
    question = state["input_question"]
    speciality = intent_analysis.get("speciality")
    
    try:
        # Recherche directe par métadonnées pour les documents TOC
        print(f"[Retrieval] Recherche TOC pour spécialité: {speciality}")
        
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
                print(f"[Retrieval] TOC trouvé: type={metadata_type}, specialite={metadata_specialite}")
        
        # Si pas assez de documents TOC, faire une recherche complémentaire
        if len(filtered_docs) < 2:
            print(f"[Retrieval] Seulement {len(filtered_docs)} docs TOC trouvés, recherche complémentaire...")
            
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
                        print(f"[Retrieval] TOC complémentaire: type={metadata_type}, specialite={metadata_specialite}")
        
        print(f"[Retrieval] {len(filtered_docs)} documents TOC récupérés au total")
        return filtered_docs[:12]  # Garder plus de documents pour une vue d'ensemble complète
        
    except Exception as e:
        print(f"[Retrieval] Erreur récupération vue d'ensemble spécialité: {e}")
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

@track_openai_call("rag_generation")
def rag_generation_node(state: IntelligentRAGState) -> Dict[str, Any]:
    """
    Génère une réponse en utilisant les documents récupérés
    """
    try:
        intent_analysis = state.get("intent_analysis")
        retrieved_docs = state.get("retrieved_docs", [])
        
        if not retrieved_docs:
            # Fallback vers RAG standard
            print("[RAG] Pas de documents, utilisation RAG standard")
            return _fallback_rag_generation(state)
        
        # Génération spécialisée selon l'intention
        if intent_analysis and intent_analysis["intent"] == IntentType.SYLLABUS_SPECIFIC_COURSE:
            return _generate_specific_course_response(state, retrieved_docs)
        elif intent_analysis and intent_analysis["intent"] == IntentType.SYLLABUS_SPECIALITY_OVERVIEW:
            return _generate_speciality_overview_response(state, retrieved_docs)
        else:
            return _generate_general_response(state, retrieved_docs)
            
    except Exception as e:
        print(f"[RAG] Erreur: {e}")
        return {
            "answer": "Je suis désolé, je rencontre une difficulté pour traiter votre demande.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["RAG generation failed"],
            "error": str(e)
        }

def _generate_general_response(state: IntelligentRAGState, docs: List[Any]) -> Dict[str, Any]:
    """Génère une réponse générale"""
    
    if not docs:
        return {
            "answer": "Je n'ai pas trouvé d'informations correspondant à votre question dans ma base de données.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["No general documents found"]
        }
    
    context_text = "\n\n".join([doc.page_content for doc in docs[:6]])
    
    prompt = f"""Tu es l'assistant de Polytech Sorbonne. Utilise les informations fournies pour répondre à la question de manière précise et utile.

Contexte (Informations générales):
{context_text}

Question: {state['input_question']}

Instructions:
- Utilise uniquement les informations du contexte
- Reste précis et factuel
- Organise ta réponse de manière claire
- Mentionne les sources spécifiques si pertinentes

Réponse:"""

    response = llm.invoke([HumanMessage(content=prompt)])
    answer = response.content.strip()
    
    # Extraire les sources
    sources = get_sources(docs) if docs else []
    
    print(f"[RAG] Réponse générale générée avec {len(docs)} documents")
    
    return {
        "answer": answer,
        "context": docs,
        "sources": sources,
        "processing_steps": state.get("processing_steps", []) + ["General response generated"]
    }

def _generate_specific_course_response(state: IntelligentRAGState, docs: List[Any]) -> Dict[str, Any]:
    """Génère une réponse spécialisée pour un cours spécifique"""
    intent_analysis = state.get("intent_analysis")
    course_name = intent_analysis.get("course_name") if intent_analysis else None
    
    if not docs:
        return {
            "answer": f"Je n'ai pas trouvé d'informations sur le cours {course_name if course_name else 'demandé'}.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["No specific course documents found"]
        }
    
    context_text = "\n\n".join([doc.page_content for doc in docs[:6]])
    
    # Utiliser l'historique si nécessaire
    history_context = ""
    if intent_analysis and intent_analysis.get("needs_history") and state.get("chat_history"):
        history_context = "\n".join([
            f"User: {msg['content']}" if msg['role'] == "user" else f"Assistant: {msg['content']}"
            for msg in state["chat_history"][-3:]  # Garder les 3 derniers échanges
        ])
        history_context = f"\n\nHistorique de conversation:\n{history_context}\n"
    
    prompt = f"""Tu es l'assistant de Polytech Sorbonne. Utilise les informations du syllabus pour répondre précisément à la question sur ce cours spécifique.

Contexte (Syllabus du cours):
{context_text}{history_context}

Question: {state['input_question']}

Instructions:
- Concentre-toi sur les détails du cours mentionné
- Inclus les objectifs pédagogiques, le programme, les modalités d'évaluation si disponibles
- Mentionne le code du cours et les prérequis si pertinents
- Sois précis et structuré dans ta réponse
- Utilise l'historique de conversation si nécessaire pour le contexte

Réponse:"""

    response = llm.invoke([HumanMessage(content=prompt)])
    answer = response.content.strip()
    
    # Extraire les sources
    sources = get_sources(docs) if docs else []
    
    print(f"[RAG] Réponse cours spécifique générée avec {len(docs)} documents")
    
    return {
        "answer": answer,
        "context": docs,
        "sources": sources,
        "processing_steps": state.get("processing_steps", []) + ["Specific course response generated"]
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
            for msg in state["chat_history"][-3:]  # Garder les 3 derniers échanges
        ])
        history_context = f"\n\nHistorique de conversation:\n{history_context}\n"
    
    speciality_name = speciality.value if speciality else "la spécialité"
    
    prompt = f"""Tu es l'assistant de Polytech Sorbonne. Utilise les informations des tables des matières et syllabus pour donner une vue d'ensemble des cours de la spécialité {speciality_name}.

Contexte (Tables des matières et syllabus):
{context_text}{history_context}

Question: {state['input_question']}

Instructions:
- Organise les cours par semestre si possible
- Donne une vue d'ensemble structurée et claire
- Mentionne les grandes thématiques et modules
- Utilise des listes à puces ou des tableaux pour la lisibilité
- Inclus les codes de cours et ECTS si disponibles
- Utilise l'historique de conversation si nécessaire pour le contexte

Réponse:"""

    response = llm.invoke([HumanMessage(content=prompt)])
    answer = response.content.strip()
    
    # Extraire les sources
    sources = get_sources(docs) if docs else []
    
    print(f"[RAG] Réponse vue d'ensemble spécialité générée avec {len(docs)} documents")
    
    return {
        "answer": answer,
        "context": docs,
        "sources": sources,
        "processing_steps": state.get("processing_steps", []) + ["Speciality overview response generated"]
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
        print(f"[RAG] Erreur fallback: {e}")
        return {
            "answer": "Je suis désolé, je ne peux pas traiter votre demande pour le moment.",
            "context": [],
            "sources": [],
            "processing_steps": state.get("processing_steps", []) + ["Fallback RAG failed"],
            "error": str(e)
        }

def _retrieve_general_docs(state: IntelligentRAGState) -> List[Any]:
    """Récupération classique pour les documents généraux (RAG standard)"""
    question = state["input_question"]
    
    try:
        # Recherche standard avec similarité
        docs = db.similarity_search(question, k=12)
        """
        # Filtrer pour EXCLURE les documents syllabus et garder les documents généraux
        filtered_docs = []
        for doc in docs:
            metadata = doc.metadata
            tags = str(metadata.get("tags", "")).lower()
            doc_type = str(metadata.get("metadata.type", "")).lower()
            document_type = str(metadata.get("document_type", "")).lower()
            
            # EXCLURE les documents de syllabus/cours pour le RAG général
            is_syllabus_doc = (
                "syllabus" in tags or
                "cours" in tags or
                doc_type in ["toc", "fiche_cours"] or
                document_type == "cours"
            )
            
            # Garder SEULEMENT les documents généraux (non-syllabus)
            if not is_syllabus_doc:
                filtered_docs.append(doc)
        
        print(f"[Retrieval] {len(filtered_docs)} documents généraux récupérés (sur {len(docs)} total)")
        return filtered_docs[:8]  # Garder les 8 meilleurs
        """
        return docs[:8]  # Garder les 8 meilleurs documents
        
    except Exception as e:
        print(f"[Retrieval] Erreur récupération générale: {e}")
        return []

# =====================================================
# Système LangGraph pour RAG avec détection d'intention
# =====================================================

# Imports des librairies nécessaires
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from pathlib import Path

# Import des composants existants
from ..llmm import initialize_the_rag_chain, llm  
from ..chat import get_sources

# ===============================================
# Récupération ou initialisation de la chaîne RAG
# ===============================================

# Variable globale pour stocker la chaîne RAG (initialisée une seule fois dans le main)
_rag_chain = None

def get_rag_chain():
    """Récupère ou initialise la chaîne RAG."""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = initialize_the_rag_chain()
    return _rag_chain  

# ===================================
# Définition de l'état du graphe RAG
# ===================================

class RAGState(TypedDict):
    input_question: str
    chat_history: List[Dict[str, str]]  # Format compatible avec ChatRequest
    intent: Optional[str]
    answer: Optional[str]
    context: Optional[List[Any]] 

# =================================================
# Fonctions de traitement pour le graphe d'état RAG
# =================================================

def intent_detection(state: RAGState) -> RAGState:
    """
    Détermine si la question nécessite du RAG ou une réponse directe.
    """
    # Conversion du format chat_history
    history_text = "".join([
        f"User: {msg['content']}\n" if msg['role'] == "user" else f"AI: {msg['content']}\n" 
        for msg in state["chat_history"]
    ])
    prompt = (
        "You are an assistant working for a university chatbot. Your task is to determine whether the user's message requires a document retrieval step (RAG) to be answered, or if it can be answered directly by the AI.\n"
        "\n"
        "Consider: the conversation history and the current user question.\n"
        "\n"
        "Rules:\n"
        "- If the question asks for specific, factual information, documents, regulations, programs, lists, or details from university resources, respond: RAG_NEEDED. This includes questions about specific programs like MAIN, AGRAL, EISE, EI2I, GM, MTX, ROB, ST, or any university-specific information.\n"
        "- If the question is general, conversational, or can be answered without documents (e.g., greetings, how the chatbot works, simple explanations), respond: DIRECT_ANSWER.\n"
        "\n"
        "Reply only with RAG_NEEDED or DIRECT_ANSWER.\n"
        "\n"
        f"History:\n{history_text}"
        f"Question:\n{state['input_question']}"
    )
    response = llm([HumanMessage(content=prompt)])
    intent = response.content.strip()
    print(f"[DEBUG] Intent: '{state['input_question']}' -> {intent}")
    return {"intent": intent}

def rag_retrieval_and_generation(state: RAGState) -> RAGState:
    """
    Récupère les documents pertinents en fonction de la question spécialisée et génère une réponse.
    """
    rag_chain = get_rag_chain()
    response = rag_chain.invoke({
        "input": state["input_question"],
        "chat_history": state["chat_history"]
    })
    answer = response.get("answer", "")
    context = response.get("context", [])
    print(f"[DEBUG] RAG response generated for: {state['input_question']}")
    return {
        "answer": answer,
        "context": context
    }

def direct_generation(state: RAGState) -> RAGState:
    """
    Génère une réponse directe pour les questions simples ne nécessitant pas de RAG.
    """
    direct_system_prompt = """You are a Polytech Sorbonne chatbot assistant. Respond in the user's language.

Handle: greetings, general questions about your role/capabilities, simple guidance.

Style: Professional, friendly, concise. Always offer help for specific Polytech questions.

For detailed institutional info (programs, admissions, etc.), acknowledge but explain you need access to official documents for accuracy."""

    prompt = f"{direct_system_prompt}\n\nQuestion: {state['input_question']}"
    response = llm([HumanMessage(content=prompt)])
    answer = response.content.strip()
    print(f"[DEBUG] Direct response generated for: {state['input_question']}")
    return {
        "answer": answer,
        "context": [] 
    }

# =======================================
# Structure du graphe d'état pour le RAG
# =======================================

def create_rag_graph():
    """Crée le graphe LangGraph qui réutilise le code existant"""
    
    builder = StateGraph(RAGState)
    
    # Ajout des nœuds
    builder.add_node("intent_detection", intent_detection)
    builder.add_node("rag_retrieval_and_generation", rag_retrieval_and_generation)
    builder.add_node("direct_generation", direct_generation)
    
    # Configuration du flux
    builder.set_entry_point("intent_detection")
    
    # Branchement conditionnel selon l'intention
    builder.add_conditional_edges(
        "intent_detection",
        lambda state: state.get("intent", "DIRECT_ANSWER"),
        {
            "RAG_NEEDED": "rag_retrieval_and_generation",
            "DIRECT_ANSWER": "direct_generation"
        }
    )
    
    builder.set_finish_point("rag_retrieval_and_generation")
    builder.set_finish_point("direct_generation")
    
    return builder.compile()

# Instance globale du graphe
rag_graph = create_rag_graph()

# ======================================
# Fonction d'interface - COMPATIBLE à 100%
# ======================================

def invoke_langgraph_rag(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interface 100% compatible avec l'ancien système.
    Retourne EXACTEMENT le même format que rag_chain.invoke()
    """
    try:
        # Conversion du format d'entrée
        langgraph_input = {
            "input_question": input_data.get("input", ""),
            "chat_history": input_data.get("chat_history", []),
        }
        
        # Exécution du graphe
        result = rag_graph.invoke(langgraph_input)
        
        # Retour dans le MÊME FORMAT que l'ancien système
        return {
            "answer": result.get("answer", ""),
            "context": result.get("context", [])  # Format IDENTIQUE pour get_sources()
        }
        
    except Exception as e:
        print(f"[ERROR] LangGraph RAG failed: {e}")
        
        # Fallback vers l'ancien système en cas d'erreur
        print("[FALLBACK] Using classic RAG system")
        rag_chain = get_rag_chain()
        return rag_chain.invoke(input_data)

# ===============
# Test du système
# ===============

if __name__ == "__main__":
    test_cases = [
        {
            "input": "Bonjour",
            "chat_history": []
        },
        {
            "input": "Quels sont les programmes MAIN ?",
            "chat_history": []
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n=== Test {i} ===")
        print(f"Input: {test['input']}")
        result = invoke_langgraph_rag(test)
        print(f"Output: {result['answer']}")
        print(f"Context count: {len(result.get('context', []))}")
        
        # Test de compatibilité avec get_sources
        from ..chat import get_sources
        sources = get_sources(result.get("context", []))
        print(f"Sources: {sources}")

        # ======================================
        # Affichage du graphe pour visualisation
        # ======================================

        output_path = Path(__file__).parent / "rag_langgraph.png"
        try:
            with open(output_path, "wb") as f:
                f.write(rag_graph.get_graph().draw_mermaid_png())
            print(f"[INFO] Graphe LangGraph sauvegardé dans : {output_path}")
        except Exception as e:
            print(f"[WARNING] Impossible de sauvegarder le graphe : {e}")

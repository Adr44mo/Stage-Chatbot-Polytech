"""
CLI pour tester le système RAG intelligent
"""

import sys
import os
from pathlib import Path
import argparse

# Add the parent directory to the path for imports

from ...app.keys_file import OPENAI_API_KEY
from ..intelligent_rag.graph import invoke_intelligent_rag
from ..intelligent_rag.state import IntentType

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

def interactive_chat():
    """Mode chat interactif"""
    cp.print_info("=" * 60)
    cp.print_info("SYSTÈME RAG INTELLIGENT - MODE INTERACTIF")
    cp.print_info("=" * 60)
    cp.print_info("Tapez 'quit' pour quitter, 'clear' pour effacer l'historique")
    cp.print_info("=" * 60)
    
    chat_history = []
    
    while True:
        try:
            question = input("\n🤔 Votre question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                cp.print_info("👋 Au revoir !")
                break
            
            if question.lower() == 'clear':
                chat_history = []
                cp.print_info("🗑️ Historique effacé")
                continue
            
            if not question:
                continue
            
            cp.print_step("🔍 Traitement en cours...")
            
            # Invoquer le système RAG intelligent
            result = invoke_intelligent_rag(question, chat_history)
            
            # Afficher les résultats
            cp.print_info(f"{'=' * 50}")
            
            if result.get("intent_analysis"):
                intent = result["intent_analysis"]["intent"]
                confidence = result["intent_analysis"]["confidence"]
                speciality = result["intent_analysis"].get("speciality")
                
                cp.print_info(f"🎯 Intention: {intent}")
                cp.print_info(f"📊 Confiance: {confidence:.2f}")
                if speciality:
                    cp.print_info(f"🎓 Spécialité: {speciality}")
            
            cp.print_info(f"✅ Succès: {result['success']}")
            
            if result.get("context"):
                cp.print_info(f"📄 Documents: {len(result['context'])}")
            
            if result.get("sources"):
                cp.print_info(f"📚 Sources: {len(result['sources'])}")
            
            cp.print_result(f"🤖 Réponse:")
            cp.print_result(f"{result['answer']}")
            
            if result.get("error"):
                cp.print_error(f"❌ Erreur: {result['error']}")
            
            # Ajouter à l'historique
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": result['answer']})
            
            cp.print_info(f"💬 Historique: {len(chat_history)} messages")
            
        except KeyboardInterrupt:
            cp.print_info("👋 Au revoir !")
            break
        except Exception as e:
            cp.print_error(f"❌ Erreur: {e}")

def batch_test(questions: list):
    """Test en lot avec une liste de questions"""
    cp.print_info("=" * 60)
    cp.print_info("SYSTÈME RAG INTELLIGENT - MODE BATCH")
    cp.print_info("=" * 60)
    
    results = []
    
    for i, question in enumerate(questions, 1):
        cp.print_step(f"--- Test {i}/{len(questions)} ---")
        cp.print_info(f"Question: {question}")
        
        try:
            result = invoke_intelligent_rag(question)
            
            intent = result.get("intent_analysis", {}).get("intent", "N/A")
            confidence = result.get("intent_analysis", {}).get("confidence", 0)
            
            cp.print_info(f"Intention: {intent} (conf: {confidence:.2f})")
            cp.print_info(f"Succès: {result['success']}")
            cp.print_info(f"Réponse: {result['answer'][:100]}...")
            
            results.append({
                "question": question,
                "intent": intent,
                "confidence": confidence,
                "success": result["success"]
            })
            
        except Exception as e:
            cp.print_error(f"Erreur: {e}")
            results.append({
                "question": question,
                "intent": "ERROR",
                "confidence": 0,
                "success": False
            })
    
    # Résumé
    cp.print_info("=" * 60)
    cp.print_info("RÉSUMÉ")
    cp.print_info("=" * 60)
    
    success_count = sum(1 for r in results if r["success"])
    
    cp.print_success(f"Tests réussis: {success_count}/{len(results)}")
    cp.print_success(f"Taux de réussite: {(success_count/len(results))*100:.1f}%")
    
    # Analyse par intention
    intent_counts = {}
    for result in results:
        intent = result["intent"]
        if intent not in intent_counts:
            intent_counts[intent] = 0
        intent_counts[intent] += 1
    
    cp.print_info("Répartition des intentions:")
    for intent, count in intent_counts.items():
        cp.print_info(f"  {intent}: {count}")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="CLI pour tester le système RAG intelligent")
    parser.add_argument("--mode", choices=["interactive", "batch", "test"], default="interactive",
                       help="Mode d'exécution")
    parser.add_argument("--questions", nargs="+", help="Questions pour le mode batch")
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        interactive_chat()
    elif args.mode == "batch":
        if not args.questions:
            cp.print_error("❌ Veuillez fournir des questions avec --questions")
            return
        batch_test(args.questions)
    elif args.mode == "test":
        # Import du module de test
        cp.print_info("🔍 pas de test...")

if __name__ == "__main__":
    main()

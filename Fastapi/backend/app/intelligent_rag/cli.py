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

def interactive_chat():
    """Mode chat interactif"""
    print("=" * 60)
    print("SYSTÈME RAG INTELLIGENT - MODE INTERACTIF")
    print("=" * 60)
    print("Tapez 'quit' pour quitter, 'clear' pour effacer l'historique")
    print("=" * 60)
    
    chat_history = []
    
    while True:
        try:
            question = input("\n🤔 Votre question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Au revoir !")
                break
            
            if question.lower() == 'clear':
                chat_history = []
                print("🗑️ Historique effacé")
                continue
            
            if not question:
                continue
            
            print("\n🔍 Traitement en cours...")
            
            # Invoquer le système RAG intelligent
            result = invoke_intelligent_rag(question, chat_history)
            
            # Afficher les résultats
            print(f"\n{'=' * 50}")
            
            if result.get("intent_analysis"):
                intent = result["intent_analysis"]["intent"]
                confidence = result["intent_analysis"]["confidence"]
                speciality = result["intent_analysis"].get("speciality")
                
                print(f"🎯 Intention: {intent}")
                print(f"📊 Confiance: {confidence:.2f}")
                if speciality:
                    print(f"🎓 Spécialité: {speciality}")
            
            print(f"✅ Succès: {result['success']}")
            
            if result.get("context"):
                print(f"📄 Documents: {len(result['context'])}")
            
            if result.get("sources"):
                print(f"📚 Sources: {len(result['sources'])}")
            
            print(f"\n🤖 Réponse:")
            print(f"{result['answer']}")
            
            if result.get("error"):
                print(f"\n❌ Erreur: {result['error']}")
            
            # Ajouter à l'historique
            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": result['answer']})
            
            print(f"\n💬 Historique: {len(chat_history)} messages")
            
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")

def batch_test(questions: list):
    """Test en lot avec une liste de questions"""
    print("=" * 60)
    print("SYSTÈME RAG INTELLIGENT - MODE BATCH")
    print("=" * 60)
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Test {i}/{len(questions)} ---")
        print(f"Question: {question}")
        
        try:
            result = invoke_intelligent_rag(question)
            
            intent = result.get("intent_analysis", {}).get("intent", "N/A")
            confidence = result.get("intent_analysis", {}).get("confidence", 0)
            
            print(f"Intention: {intent} (conf: {confidence:.2f})")
            print(f"Succès: {result['success']}")
            print(f"Réponse: {result['answer'][:100]}...")
            
            results.append({
                "question": question,
                "intent": intent,
                "confidence": confidence,
                "success": result["success"]
            })
            
        except Exception as e:
            print(f"Erreur: {e}")
            results.append({
                "question": question,
                "intent": "ERROR",
                "confidence": 0,
                "success": False
            })
    
    # Résumé
    print(f"\n{'=' * 60}")
    print("RÉSUMÉ")
    print(f"{'=' * 60}")
    
    success_count = sum(1 for r in results if r["success"])
    
    print(f"Tests réussis: {success_count}/{len(results)}")
    print(f"Taux de réussite: {(success_count/len(results))*100:.1f}%")
    
    # Analyse par intention
    intent_counts = {}
    for result in results:
        intent = result["intent"]
        if intent not in intent_counts:
            intent_counts[intent] = 0
        intent_counts[intent] += 1
    
    print("\nRépartition des intentions:")
    for intent, count in intent_counts.items():
        print(f"  {intent}: {count}")

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
            print("❌ Veuillez fournir des questions avec --questions")
            return
        batch_test(args.questions)
    elif args.mode == "test":
        # Import du module de test
        print("🔍 pas de test...")

if __name__ == "__main__":
    main()

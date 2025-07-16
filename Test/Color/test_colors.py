#!/usr/bin/env python3
"""
Script de test pour la nouvelle classe ColorPrint
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from colored_print import ColorPrint

def test_colored_output():
    """Test des différents types de messages colorés"""
    
    ColorPrint.print_header("Test du Système de Couleurs - RAG Intelligent")
    
    # Test des types de base
    ColorPrint.print_info("Initialisation du système RAG intelligent")
    ColorPrint.print_success("Configuration chargée avec succès")
    ColorPrint.print_warning("Attention: Utilisation d'un modèle de test")
    ColorPrint.print_error("Erreur: Impossible de se connecter à la base de données")
    ColorPrint.print_debug("Variables d'environnement: OPENAI_API_KEY=***")
    
    ColorPrint.print_separator()
    
    # Test des nouveaux types
    ColorPrint.print_step("Analyse d'intention en cours...", 1)
    ColorPrint.print_step("Récupération des documents", 2)
    ColorPrint.print_step("Génération de la réponse", 3)
    
    ColorPrint.print_separator()
    
    # Test des métriques
    ColorPrint.print_cost("Coût total: $0.0234 (156 tokens)")
    ColorPrint.print_performance("Temps de réponse: 2.34 secondes")
    ColorPrint.print_api("POST /intelligent-rag/chat - Status: 200")
    
    ColorPrint.print_separator()
    
    # Test des résultats
    ColorPrint.print_result("Intention détectée: SYLLABUS_SPECIALITY_OVERVIEW")
    ColorPrint.print_result("Spécialité: ROB (Robotique)")
    ColorPrint.print_result("Documents trouvés: 12")
    
    ColorPrint.print_separator()
    
    # Exemple d'utilisation dans un contexte réel
    ColorPrint.print_info("Démarrage du test d'intégration")
    ColorPrint.print_step("Connexion à l'API", 1)
    ColorPrint.print_api("GET /intelligent-rag/health - Testing...")
    ColorPrint.print_success("API accessible")
    
    ColorPrint.print_step("Test d'une question", 2)
    ColorPrint.print_info("Question: 'Quels sont les cours de robotique ?'")
    ColorPrint.print_performance("Analyse d'intention: 0.05s")
    ColorPrint.print_performance("Récupération documents: 0.12s")
    ColorPrint.print_performance("Génération réponse: 1.89s")
    ColorPrint.print_cost("Coût de la requête: $0.0187")
    
    ColorPrint.print_result("Réponse générée avec succès (2847 caractères)")
    ColorPrint.print_success("Test d'intégration terminé avec succès")
    
    ColorPrint.print_separator('=')
    
    print("\n✨ Exemple d'utilisation dans le code :")
    print("```python")
    print("from Test.Color.colored_print import ColorPrint")
    print("")
    print("# Messages informatifs")
    print("ColorPrint.print_info('Démarrage du système RAG')")
    print("ColorPrint.print_step('Analyse d\\'intention', 1)")
    print("ColorPrint.print_cost('Coût: $0.0234')")
    print("ColorPrint.print_success('Réponse générée')")
    print("```")

if __name__ == "__main__":
    test_colored_output()

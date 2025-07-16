#!/usr/bin/env python3
"""
Script pour générer un diagramme détaillé du processus LangGraph RAG
Ce script crée un diagramme de flux complet pour le README.md
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np
from color_utils import cp

def create_langgraph_diagram():
    """Crée un diagramme détaillé du processus LangGraph"""
    
    # Configuration de la figure
    fig, ax = plt.subplots(1, 1, figsize=(16, 20))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 25)
    ax.axis('off')
    
    # Couleurs pour les différents types de nœuds
    colors = {
        'entry': '#4CAF50',      # Vert - Point d'entrée
        'process': '#2196F3',    # Bleu - Traitement
        'decision': '#FF9800',   # Orange - Décision
        'output': '#9C27B0',     # Violet - Sortie
        'error': '#F44336',      # Rouge - Erreur
        'end': '#607D8B'         # Gris - Fin
    }
    
    # Fonction pour créer un nœud
    def create_node(x, y, width, height, text, color, text_color='white', fontsize=9):
        # Création du rectangle arrondi
        box = FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(box)
        
        # Ajout du texte
        ax.text(x, y, text, ha='center', va='center', 
                fontsize=fontsize, color=text_color, weight='bold',
                wrap=True)
        
        return box
    
    # Fonction pour créer une flèche
    def create_arrow(start_x, start_y, end_x, end_y, text='', offset=0.2):
        arrow = ConnectionPatch(
            (start_x, start_y), (end_x, end_y),
            "data", "data",
            arrowstyle="->",
            shrinkA=0, shrinkB=0,
            mutation_scale=20,
            fc="black"
        )
        ax.add_patch(arrow)
        
        # Ajout du texte sur la flèche si nécessaire
        if text:
            mid_x = (start_x + end_x) / 2 + offset
            mid_y = (start_y + end_y) / 2
            ax.text(mid_x, mid_y, text, ha='center', va='center',
                   fontsize=8, bbox=dict(boxstyle="round,pad=0.3", 
                   facecolor='white', alpha=0.8))
    
    # Titre principal
    ax.text(5, 24, 'Architecture du Système RAG - LangGraph', 
            ha='center', va='center', fontsize=18, weight='bold')
    
    # Sous-titre
    ax.text(5, 23.2, 'Processus de traitement des documents avec étapes détaillées', 
            ha='center', va='center', fontsize=12, style='italic')
    
    # === NIVEAU 1: POINT D'ENTRÉE ===
    create_node(5, 22, 3, 0.8, 'POINT D\'ENTRÉE\ncheck_type_of_input', colors['entry'])
    
    # === NIVEAU 2: ANALYSE DU TYPE D'ENTRÉE ===
    ax.text(5, 20.8, 'Analyse du type de fichier d\'entrée', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    # Nœuds de décision pour les différents types
    create_node(1.5, 19.5, 2.5, 1, 'Fichier JSON\n(web_page = True\npdf_scraped = False)', colors['decision'])
    create_node(3.5, 19.5, 2.5, 1, 'PDF Scrapé\n(pdf_scraped = True)', colors['decision'])
    create_node(6.5, 19.5, 2.5, 1, 'Syllabus\n(is_syllabus = True)', colors['decision'])
    create_node(8.5, 19.5, 2.5, 1, 'PDF Manuel\n(défaut)', colors['decision'])
    
    # Flèches du point d'entrée vers les décisions
    create_arrow(4, 21.6, 1.5, 20.3, 'JSON')
    create_arrow(4.5, 21.6, 3.5, 20.3, 'PDF Scrapé')
    create_arrow(5.5, 21.6, 6.5, 20.3, 'Syllabus')
    create_arrow(6, 21.6, 8.5, 20.3, 'PDF Manuel')
    
    # === NIVEAU 3: TRAITEMENT SPÉCIALISÉ ===
    ax.text(5, 17.8, 'Traitement spécialisé selon le type', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    # Nœuds de traitement spécialisé
    create_node(1.5, 17, 2.5, 1, 'Normalisation\nnormalize_json_file\n(Site web)', colors['process'])
    create_node(3.5, 17, 2.5, 1, 'Chargement\nload_pdf_scraped\n(PDF scrapé)', colors['process'])
    create_node(6.5, 17, 2.5, 1, 'Extraction\nsyllabus_extract\n(Structure syllabus)', colors['process'])
    create_node(8.5, 17, 2.5, 1, 'Chargement\nload_pdf_manual\n(PDF manuel)', colors['process'])
    
    # Flèches vers les traitements spécialisés
    create_arrow(1.5, 18.7, 1.5, 17.8)
    create_arrow(3.5, 18.7, 3.5, 17.8)
    create_arrow(6.5, 18.7, 6.5, 17.8)
    create_arrow(8.5, 18.7, 8.5, 17.8)
    
    # === NIVEAU 4: ENRICHISSEMENT DES MÉTADONNÉES ===
    ax.text(5, 15.3, 'Enrichissement des métadonnées', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    # Nœuds d'enrichissement
    create_node(2.5, 14.5, 2.5, 1, 'Métadonnées\nfill_metadata_scraped\n(Données scrapées)', colors['process'])
    create_node(7.5, 14.5, 2.5, 1, 'Métadonnées\nfill_metadata_manual\n(Saisie manuelle)', colors['process'])
    
    # Flèches vers l'enrichissement
    create_arrow(1.5, 16.2, 2.5, 15.3, 'JSON → Métadonnées')
    create_arrow(3.5, 16.2, 2.5, 15.3, 'PDF Scrapé → Métadonnées')
    create_arrow(8.5, 16.2, 7.5, 15.3, 'PDF Manuel → Métadonnées')
    
    # === NIVEAU 5: CONVERGENCE - AJOUT DES TAGS ===
    ax.text(5, 12.8, 'Convergence et ajout des tags', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    create_node(5, 12, 3, 1, 'Ajout des Tags\nfill_tags\n(Classification automatique)', colors['process'])
    
    # Flèches vers l'ajout des tags
    create_arrow(1.5, 16.2, 4, 12.8, 'JSON Direct')
    create_arrow(2.5, 13.7, 4, 12.8)
    create_arrow(6.5, 16.2, 6, 12.8, 'Syllabus Direct')
    create_arrow(7.5, 13.7, 6, 12.8)
    
    # === NIVEAU 6: VALIDATION ===
    ax.text(5, 10.3, 'Validation et contrôle qualité', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    create_node(5, 9.5, 3, 1, 'Validation\nvalidate_node\n(Schéma + Règles)', colors['decision'])
    
    # Flèche vers la validation
    create_arrow(5, 11.2, 5, 10.3)
    
    # === NIVEAU 7: SAUVEGARDE ===
    ax.text(5, 7.8, 'Sauvegarde selon le résultat de validation', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    create_node(3, 7, 2.5, 1, 'Sauvegarde\nsave_node\n(Documents valides)', colors['output'])
    create_node(7, 7, 2.5, 1, 'Sauvegarde Erreur\nsave_to_error_node\n(Documents rejetés)', colors['error'])
    
    # Flèches conditionnelles
    create_arrow(4.2, 8.7, 3.5, 7.8, 'Valide')
    create_arrow(5.8, 8.7, 6.5, 7.8, 'Invalide')
    
    # === NIVEAU 8: FINALISATION ===
    ax.text(5, 5.3, 'Finalisation et nettoyage', ha='center', va='center', 
            fontsize=10, weight='bold', style='italic')
    
    create_node(5, 4.5, 3, 1, 'Finalisation\nend_node\n(Statistiques + Nettoyage)', colors['end'])
    
    # Flèches vers la finalisation
    create_arrow(3, 6.2, 4, 5.3)
    create_arrow(7, 6.2, 6, 5.3)
    
    # === INFORMATIONS SUPPLÉMENTAIRES ===
    # Légende
    legend_y = 2.5
    ax.text(1, legend_y + 0.5, 'Légende:', ha='left', va='center', 
            fontsize=12, weight='bold')
    
    legend_items = [
        ('Point d\'entrée', colors['entry']),
        ('Traitement', colors['process']),
        ('Décision', colors['decision']),
        ('Sortie', colors['output']),
        ('Erreur', colors['error']),
        ('Fin', colors['end'])
    ]
    
    for i, (text, color) in enumerate(legend_items):
        y_pos = legend_y - i * 0.3
        create_node(1.5, y_pos, 0.3, 0.2, '', color)
        ax.text(1.8, y_pos, text, ha='left', va='center', fontsize=10)
    
    # Informations sur l'état
    ax.text(6, legend_y + 0.5, 'État partagé (FillerState):', ha='left', va='center', 
            fontsize=12, weight='bold')
    
    state_info = [
        '• file_path: Chemin du fichier',
        '• data: Données extraites',
        '• output_data: Données formatées',
        '• is_valid: Statut de validation',
        '• web_page: Origine web',
        '• pdf_scraped: PDF scrapé',
        '• is_syllabus: Type syllabus',
        '• error/traceback: Gestion erreurs'
    ]
    
    for i, text in enumerate(state_info):
        y_pos = legend_y - i * 0.2
        ax.text(6, y_pos, text, ha='left', va='center', fontsize=9)
    
    # Sauvegarde
    plt.tight_layout()
    plt.savefig('/srv/partage/Stage-Chatbot-Polytech/docs/langgraph_architecture.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('/srv/partage/Stage-Chatbot-Polytech/docs/langgraph_architecture.pdf', 
                bbox_inches='tight', facecolor='white')
    
    cp.print_success("Diagramme LangGraph généré avec succès!")
    cp.print_info("Fichiers créés:")
    cp.print_info("  • docs/langgraph_architecture.png")
    cp.print_info("  • docs/langgraph_architecture.pdf")

def create_detailed_flow_diagram():
    """Crée un diagramme de flux détaillé avec étapes numérotées"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 18))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 20)
    ax.axis('off')
    
    # Couleurs par étape
    step_colors = ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3', '#1E88E5', '#1976D2']
    
    # Titre
    ax.text(5, 19.5, 'Processus RAG - Flux Détaillé par Étapes', 
            ha='center', va='center', fontsize=16, weight='bold')
    
    # Fonction pour créer une flèche
    def create_arrow(start_x, start_y, end_x, end_y):
        arrow = ConnectionPatch(
            (start_x, start_y), (end_x, end_y),
            "data", "data",
            arrowstyle="->",
            shrinkA=5, shrinkB=5,
            mutation_scale=20,
            fc="#1976D2",
            ec="#1976D2",
            linewidth=2
        )
        ax.add_patch(arrow)
    
    # Fonction pour créer une étape
    def create_step(x, y, width, height, step_num, title, description, color):
        # Boîte principale
        box = FancyBboxPatch(
            (x - width/2, y - height/2), width, height,
            boxstyle="round,pad=0.15",
            facecolor=color,
            edgecolor='#1976D2',
            linewidth=2
        )
        ax.add_patch(box)
        
        # Numéro d'étape
        circle = plt.Circle((x - width/2 + 0.4, y + height/2 - 0.3), 0.2, 
                          color='#1976D2', zorder=10)
        ax.add_patch(circle)
        ax.text(x - width/2 + 0.4, y + height/2 - 0.3, str(step_num), 
               ha='center', va='center', fontsize=12, weight='bold', color='white')
        
        # Titre
        ax.text(x, y + 0.2, title, ha='center', va='center', 
                fontsize=11, weight='bold', color='#1976D2')
        
        # Description
        ax.text(x, y - 0.2, description, ha='center', va='center', 
                fontsize=9, color='#424242', wrap=True)
    
    # Étapes du processus
    steps = [
        (5, 18, 8, 1, 1, "Analyse du Type d'Entrée", "Détection automatique du type de fichier\n(JSON, PDF scrapé, Syllabus, PDF manuel)"),
        (5, 16.5, 8, 1, 2, "Chargement des Données", "Extraction du contenu selon le type\n(Parser JSON, OCR PDF, extraction texte)"),
        (5, 15, 8, 1, 3, "Détection du Type de Document", "Classification automatique du contenu\n(cours, administratif, spécialité, projet...)"),
        (5, 13.5, 8, 1, 4, "Enrichissement des Métadonnées", "Ajout des informations manquantes\n(titre, auteur, date, secteur...)"),
        (5, 12, 8, 1, 5, "Classification et Tags", "Attribution automatique de tags\n(mots-clés, catégories, domaines)"),
        (5, 10.5, 8, 1, 6, "Validation et Contrôle", "Vérification de la conformité\n(schéma, règles métier, qualité)"),
        (5, 9, 8, 1, 7, "Sauvegarde et Indexation", "Stockage dans la base vectorielle\n(embedding, métadonnées, indexation)"),
        (5, 7.5, 8, 1, 8, "Finalisation et Statistiques", "Nettoyage et rapport de traitement\n(métriques, logs, statut final)")
    ]
    
    for i, (x, y, w, h, num, title, desc) in enumerate(steps):
        create_step(x, y, w, h, num, title, desc, step_colors[i])
        
        # Flèche vers l'étape suivante
        if i < len(steps) - 1:
            create_arrow(x, y - h/2, x, steps[i+1][1] + h/2)
    
    # Informations techniques
    ax.text(5, 6, 'Technologies Utilisées', ha='center', va='center', 
            fontsize=14, weight='bold', color='#1976D2')
    
    tech_info = [
        "LangGraph: Orchestration du workflow",
        "OpenAI GPT-4: Intelligence artificielle",
        "ChromaDB: Base de données vectorielle",
        "Embedding: Représentation sémantique",
        "PyPDF2: Extraction de texte PDF",
        "Pydantic: Validation des données"
    ]
    
    for i, tech in enumerate(tech_info):
        y_pos = 5.5 - i * 0.3
        ax.text(5, y_pos, tech, ha='center', va='center', fontsize=10)
    
    # Sauvegarde
    plt.tight_layout()
    plt.savefig('/srv/partage/Stage-Chatbot-Polytech/docs/detailed_flow.png', 
                dpi=300, bbox_inches='tight', facecolor='white')
    
    cp.print_success("Diagramme de flux détaillé généré!")

if __name__ == "__main__":
    cp.print_header("Génération des diagrammes LangGraph")
    
    # Création des diagrammes
    create_langgraph_diagram()
    create_detailed_flow_diagram()
    
    cp.print_success("Tous les diagrammes ont été générés avec succès!")
    cp.print_info("Vous pouvez maintenant les inclure dans votre README.md")

"""
Visualiseur de graphe pour le système RAG intelligent
"""

import os
from pathlib import Path
from typing import Optional

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    print("⚠️ Graphviz non disponible. Installez avec: pip install graphviz")

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
    import networkx as nx
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib non disponible. Installez avec: pip install matplotlib networkx")

from ...app.keys_file import OPENAI_API_KEY
from .state import IntentType
from .graph import create_intelligent_rag_graph

def create_graph_visualization_graphviz(output_path: Optional[str] = None) -> str:
    """
    Crée une visualisation du graphe avec Graphviz
    """
    if not GRAPHVIZ_AVAILABLE:
        raise ImportError("Graphviz n'est pas disponible")
    
    # Créer le graphe Graphviz
    dot = graphviz.Digraph(comment='Intelligent RAG System')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='rounded,filled')
    
    # Définir les couleurs
    colors = {
        'entry': '#e8f5e8',
        'analysis': '#fff2cc', 
        'decision': '#ffe6cc',
        'direct': '#d4edda',
        'retrieval': '#cce5ff',
        'generation': '#f8d7da',
        'finish': '#e2e3e5'
    }
    
    # Nœuds
    dot.node('start', 'DÉBUT', fillcolor=colors['entry'])
    dot.node('intent_analysis', 'Analyse d\'Intention\n(OpenAI + JSON)', fillcolor=colors['analysis'])
    dot.node('router', 'Routeur\nConditionnel', fillcolor=colors['decision'], shape='diamond')
    dot.node('direct_answer', 'Réponse Directe\n(Pas de RAG)', fillcolor=colors['direct'])
    dot.node('document_retrieval', 'Récupération\nDocuments', fillcolor=colors['retrieval'])
    dot.node('rag_generation', 'Génération RAG\n(Avec contexte)', fillcolor=colors['generation'])
    dot.node('end_direct', 'FIN\n(Direct)', fillcolor=colors['finish'])
    dot.node('end_rag', 'FIN\n(RAG)', fillcolor=colors['finish'])
    
    # Arêtes principales
    dot.edge('start', 'intent_analysis', 'Question +\nHistorique')
    dot.edge('intent_analysis', 'router', 'Intent Analysis')
    
    # Branchements conditionnels
    dot.edge('router', 'direct_answer', 'DIRECT_ANSWER\n(Salutations, etc.)', color='green')
    dot.edge('router', 'document_retrieval', 'RAG_NEEDED\n+ SYLLABUS_TOC', color='blue')
    
    # Continuations
    dot.edge('document_retrieval', 'rag_generation', 'Documents')
    dot.edge('direct_answer', 'end_direct')
    dot.edge('rag_generation', 'end_rag')
    
    # Sous-graphe pour les intentions
    with dot.subgraph(name='cluster_intentions') as s:
        s.attr(label='Types d\'Intentions')
        s.attr(color='lightgrey')
        s.node('direct_intent', 'DIRECT_ANSWER\\n• Salutations\\n• Remerciements\\n• Questions générales', 
               fillcolor='#d4edda', shape='note')
        s.node('rag_intent', 'RAG_NEEDED\\n• Associations\\n• Inscriptions\\n• Campus\\n• Débouchés', 
               fillcolor='#cce5ff', shape='note')
        s.node('syllabus_intent', 'SYLLABUS_TOC\\n• Programmes\\n• Cours\\n• Tables des matières\\n• Spécialités', 
               fillcolor='#fff2cc', shape='note')
    
    # Sauvegarder
    if not output_path:
        output_path = Path(__file__).parent / "logs" / "graph_visualization"
    
    output_file = str(output_path)
    dot.render(output_file, format='png', cleanup=True)
    dot.render(output_file, format='svg', cleanup=True)
    
    print(f"✅ Graphe sauvegardé: {output_file}.png et {output_file}.svg")
    return f"{output_file}.png"

def create_graph_visualization_matplotlib(output_path: Optional[str] = None) -> str:
    """
    Crée une visualisation du graphe avec Matplotlib
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("Matplotlib n'est pas disponible")
    
    # Créer le graphe NetworkX
    G = nx.DiGraph()
    
    # Ajouter les nœuds avec leurs types
    nodes = {
        'start': {'type': 'entry', 'label': 'DÉBUT'},
        'intent_analysis': {'type': 'analysis', 'label': 'Analyse\nIntention'},
        'router': {'type': 'decision', 'label': 'Routeur'},
        'direct_answer': {'type': 'direct', 'label': 'Réponse\nDirecte'},
        'document_retrieval': {'type': 'retrieval', 'label': 'Récupération\nDocuments'},
        'rag_generation': {'type': 'generation', 'label': 'Génération\nRAG'},
        'end_direct': {'type': 'finish', 'label': 'FIN\n(Direct)'},
        'end_rag': {'type': 'finish', 'label': 'FIN\n(RAG)'}
    }
    
    for node_id, attrs in nodes.items():
        G.add_node(node_id, **attrs)
    
    # Ajouter les arêtes
    edges = [
        ('start', 'intent_analysis', 'Question'),
        ('intent_analysis', 'router', 'Analysis'),
        ('router', 'direct_answer', 'DIRECT'),
        ('router', 'document_retrieval', 'RAG_NEEDED\nSYLLABUS_TOC'),
        ('document_retrieval', 'rag_generation', 'Documents'),
        ('direct_answer', 'end_direct', ''),
        ('rag_generation', 'end_rag', '')
    ]
    
    for source, target, label in edges:
        G.add_edge(source, target, label=label)
    
    # Configuration de la figure
    plt.figure(figsize=(14, 10))
    plt.title('Système RAG Intelligent - Architecture', fontsize=16, fontweight='bold', pad=20)
    
    # Position des nœuds
    pos = {
        'start': (0, 4),
        'intent_analysis': (0, 3),
        'router': (0, 2),
        'direct_answer': (-2, 1),
        'document_retrieval': (2, 1),
        'rag_generation': (2, 0),
        'end_direct': (-2, 0),
        'end_rag': (2, -1)
    }
    
    # Couleurs par type
    colors = {
        'entry': '#e8f5e8',
        'analysis': '#fff2cc',
        'decision': '#ffe6cc',
        'direct': '#d4edda',
        'retrieval': '#cce5ff',
        'generation': '#f8d7da',
        'finish': '#e2e3e5'
    }
    
    # Dessiner les nœuds
    for node_id, (x, y) in pos.items():
        node_data = G.nodes[node_id]
        color = colors[node_data['type']]
        
        if node_data['type'] == 'decision':
            # Diamant pour le routeur
            bbox = dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor='black', linewidth=2)
        else:
            # Rectangle arrondi pour les autres
            bbox = dict(boxstyle="round,pad=0.5", facecolor=color, edgecolor='black', linewidth=1)
        
        plt.text(x, y, node_data['label'], ha='center', va='center', 
                fontsize=10, fontweight='bold', bbox=bbox)
    
    # Dessiner les arêtes
    for source, target, edge_data in G.edges(data=True):
        x1, y1 = pos[source]
        x2, y2 = pos[target]
        
        # Couleur de l'arête selon le type
        if 'DIRECT' in edge_data['label']:
            edge_color = 'green'
            linewidth = 2
        elif 'RAG' in edge_data['label']:
            edge_color = 'blue'
            linewidth = 2
        else:
            edge_color = 'black'
            linewidth = 1
        
        # Flèche
        plt.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=edge_color, linewidth=linewidth))
        
        # Label de l'arête
        if edge_data['label']:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            plt.text(mid_x + 0.1, mid_y + 0.1, edge_data['label'], 
                    fontsize=8, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # Légende
    legend_elements = [
        mpatches.Patch(color=colors['entry'], label='Point d\'entrée'),
        mpatches.Patch(color=colors['analysis'], label='Analyse'),
        mpatches.Patch(color=colors['decision'], label='Décision'),
        mpatches.Patch(color=colors['direct'], label='Réponse directe'),
        mpatches.Patch(color=colors['retrieval'], label='Récupération'),
        mpatches.Patch(color=colors['generation'], label='Génération'),
        mpatches.Patch(color=colors['finish'], label='Fin')
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))
    
    # Configuration des axes
    plt.xlim(-3.5, 3.5)
    plt.ylim(-2, 5)
    plt.axis('off')
    plt.tight_layout()
    
    # Sauvegarder
    if not output_path:
        output_path = Path(__file__).parent / "logs" / "graph_visualization_matplotlib.png"
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Graphe Matplotlib sauvegardé: {output_path}")
    return str(output_path)

def create_detailed_flow_diagram(output_path: Optional[str] = None) -> str:
    """
    Crée un diagramme de flux détaillé avec les étapes spécifiques
    """
    if not GRAPHVIZ_AVAILABLE:
        raise ImportError("Graphviz n'est pas disponible")
    
    dot = graphviz.Digraph(comment='Flux détaillé RAG Intelligent')
    dot.attr(rankdir='TB', size='16,20')
    dot.attr('node', shape='box', style='rounded,filled')
    
    # Couleurs spécialisées
    colors = {
        'input': '#e8f5e8',
        'llm': '#fff2cc',
        'logic': '#ffe6cc',
        'search': '#cce5ff',
        'output': '#f8d7da'
    }
    
    # Flux principal
    dot.node('user_input', 'Question\nUtilisateur', fillcolor=colors['input'])
    dot.node('history_build', 'Construction\nHistorique', fillcolor=colors['logic'])
    dot.node('openai_intent', 'OpenAI API\n(gpt-4o-mini)\nAnalyse JSON', fillcolor=colors['llm'])
    dot.node('json_parse', 'Parsing JSON\n+ Validation', fillcolor=colors['logic'])
    
    # Branchement
    dot.node('decision', 'Type d\'Intention?', fillcolor=colors['logic'], shape='diamond')
    
    # Branche DIRECT_ANSWER
    dot.node('direct_prompt', 'Prompt Direct\n(Pas de RAG)', fillcolor=colors['llm'])
    dot.node('direct_response', 'Réponse\nDirecte', fillcolor=colors['output'])
    
    # Branche RAG
    dot.node('doc_strategy', 'Stratégie de\nRecherche', fillcolor=colors['logic'])
    dot.node('syllabus_search', 'Recherche\nSyllabus/TOC', fillcolor=colors['search'])
    dot.node('general_search', 'Recherche\nGénérale', fillcolor=colors['search'])
    dot.node('doc_filter', 'Filtrage\nDocuments', fillcolor=colors['logic'])
    dot.node('context_build', 'Construction\nContexte', fillcolor=colors['logic'])
    dot.node('rag_prompt', 'Prompt RAG\n+ Contexte', fillcolor=colors['llm'])
    dot.node('rag_response', 'Réponse\nRAG', fillcolor=colors['output'])
    
    # Logging et stats
    dot.node('token_count', 'Comptage\nTokens', fillcolor='#f0f0f0')
    dot.node('save_log', 'Sauvegarde\nLogs', fillcolor='#f0f0f0')
    
    # Flux principal
    dot.edge('user_input', 'history_build')
    dot.edge('history_build', 'openai_intent')
    dot.edge('openai_intent', 'json_parse')
    dot.edge('json_parse', 'decision')
    
    # Branche directe
    dot.edge('decision', 'direct_prompt', 'DIRECT_ANSWER', color='green')
    dot.edge('direct_prompt', 'direct_response')
    dot.edge('direct_response', 'token_count')
    
    # Branche RAG
    dot.edge('decision', 'doc_strategy', 'RAG_NEEDED\nSYLLABUS_TOC', color='blue')
    dot.edge('doc_strategy', 'syllabus_search', 'Si SYLLABUS_TOC')
    dot.edge('doc_strategy', 'general_search', 'Si RAG_NEEDED')
    dot.edge('syllabus_search', 'doc_filter')
    dot.edge('general_search', 'doc_filter')
    dot.edge('doc_filter', 'context_build')
    dot.edge('context_build', 'rag_prompt')
    dot.edge('rag_prompt', 'rag_response')
    dot.edge('rag_response', 'token_count')
    
    # Logging
    dot.edge('token_count', 'save_log')
    
    # Sauvegarder
    if not output_path:
        output_path = Path(__file__).parent / "logs" / "detailed_flow"
    
    output_file = str(output_path)
    dot.render(output_file, format='png', cleanup=True)
    print(f"✅ Flux détaillé sauvegardé: {output_file}.png")
    return f"{output_file}.png"

def generate_all_visualizations(output_dir: Optional[str] = None):
    """
    Génère toutes les visualisations disponibles
    """
    if not output_dir:
        output_dir = Path(__file__).parent / "logs"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    print("🎨 Génération des visualisations du système RAG intelligent...")
    
    # Graphe principal avec Graphviz
    if GRAPHVIZ_AVAILABLE:
        try:
            file_path = create_graph_visualization_graphviz(output_dir / "main_graph")
            generated_files.append(file_path)
        except Exception as e:
            print(f"❌ Erreur Graphviz principal: {e}")
    
    # Graphe avec Matplotlib
    if MATPLOTLIB_AVAILABLE:
        try:
            file_path = create_graph_visualization_matplotlib(output_dir / "main_graph_matplotlib.png")
            generated_files.append(file_path)
        except Exception as e:
            print(f"❌ Erreur Matplotlib: {e}")
    
    # Flux détaillé
    if GRAPHVIZ_AVAILABLE:
        try:
            file_path = create_detailed_flow_diagram(output_dir / "detailed_flow")
            generated_files.append(file_path)
        except Exception as e:
            print(f"❌ Erreur flux détaillé: {e}")
    
    print(f"✅ {len(generated_files)} visualisations générées:")
    for file_path in generated_files:
        print(f"   📁 {file_path}")
    
    return generated_files

if __name__ == "__main__":
    # Génération de toutes les visualisations
    generate_all_visualizations()

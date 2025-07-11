import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# Configuration du style
plt.style.use('default')
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Couleurs
colors = {
    'user': '#3498db',
    'api': '#2ecc71', 
    'intelligence': '#e74c3c',
    'retrieval': '#f39c12',
    'llm': '#9b59b6',
    'storage': '#34495e',
    'monitoring': '#1abc9c'
}

# Titre
title = ax.text(5, 11.5, 'Architecture du Système RAG Intelligent - Polytech Sorbonne', 
               fontsize=20, fontweight='bold', ha='center')

# 1. User Interface Layer
user_box = FancyBboxPatch((0.5, 10), 2, 1, boxstyle="round,pad=0.1", 
                         facecolor=colors['user'], alpha=0.7, edgecolor='black')
ax.add_patch(user_box)
ax.text(1.5, 10.5, 'Interface\nUtilisateur', fontsize=12, fontweight='bold', 
        ha='center', va='center', color='white')

# 2. API Layer
api_box = FancyBboxPatch((0.5, 8.5), 2, 1, boxstyle="round,pad=0.1",
                        facecolor=colors['api'], alpha=0.7, edgecolor='black')
ax.add_patch(api_box)
ax.text(1.5, 9, 'FastAPI\nEndpoints', fontsize=12, fontweight='bold',
        ha='center', va='center', color='white')

# 3. Intelligence Layer (Le cœur du système)
intel_box = FancyBboxPatch((3.5, 7.5), 3, 2.5, boxstyle="round,pad=0.1",
                          facecolor=colors['intelligence'], alpha=0.7, edgecolor='black')
ax.add_patch(intel_box)
ax.text(5, 9.5, 'SYSTÈME RAG INTELLIGENT', fontsize=14, fontweight='bold',
        ha='center', va='center', color='white')

# Sub-composants du système intelligent
ax.text(5, 9, '1. Analyse d\'Intention (LLM)', fontsize=10, ha='center', va='center', color='white')
ax.text(5, 8.6, '2. Routage Intelligent', fontsize=10, ha='center', va='center', color='white')
ax.text(5, 8.2, '3. Récupération Spécialisée', fontsize=10, ha='center', va='center', color='white')
ax.text(5, 7.8, '4. Génération Contextuelle', fontsize=10, ha='center', va='center', color='white')

# 4. Retrieval Strategies
strategies = [
    ('RAG Général\n(Témoignages)', 1, 6),
    ('Cours Spécifique\n(Syllabus)', 3, 6),
    ('Vue d\'Ensemble\n(TOC)', 5, 6),
    ('Réponse Directe\n(Sans RAG)', 7, 6)
]

for name, x, y in strategies:
    strategy_box = FancyBboxPatch((x-0.7, y-0.4), 1.4, 0.8, boxstyle="round,pad=0.1",
                                 facecolor=colors['retrieval'], alpha=0.7, edgecolor='black')
    ax.add_patch(strategy_box)
    ax.text(x, y, name, fontsize=9, fontweight='bold', ha='center', va='center', color='white')

# 5. LLM Processing
llm_box = FancyBboxPatch((7.5, 8.5), 2, 1, boxstyle="round,pad=0.1",
                        facecolor=colors['llm'], alpha=0.7, edgecolor='black')
ax.add_patch(llm_box)
ax.text(8.5, 9, 'OpenAI\nGPT-4o-mini', fontsize=12, fontweight='bold',
        ha='center', va='center', color='white')

# 6. Storage Layer
storage_boxes = [
    ('ChromaDB\nVectorstore', 1, 4),
    ('Logs JSON\nStatistiques', 5, 4),
    ('Documents\nSources', 8, 4)
]

for name, x, y in storage_boxes:
    storage_box = FancyBboxPatch((x-0.7, y-0.4), 1.4, 0.8, boxstyle="round,pad=0.1",
                                facecolor=colors['storage'], alpha=0.7, edgecolor='black')
    ax.add_patch(storage_box)
    ax.text(x, y, name, fontsize=9, fontweight='bold', ha='center', va='center', color='white')

# 7. Monitoring Layer
monitoring_box = FancyBboxPatch((0.5, 2), 8.5, 1, boxstyle="round,pad=0.1",
                               facecolor=colors['monitoring'], alpha=0.7, edgecolor='black')
ax.add_patch(monitoring_box)
ax.text(4.75, 2.5, 'MONITORING & ANALYTICS', fontsize=14, fontweight='bold',
        ha='center', va='center', color='white')

# Détails du monitoring
monitoring_details = [
    'Token Cost Tracking', 'Performance Metrics', 'Intent Classification Stats',
    'Response Quality', 'Error Monitoring', 'Daily Reports'
]
for i, detail in enumerate(monitoring_details):
    x_pos = 1 + (i % 3) * 2.5
    y_pos = 2.3 if i < 3 else 2.1
    ax.text(x_pos, y_pos, f'• {detail}', fontsize=8, ha='left', va='center', color='white')

# Flèches de connexion
arrows = [
    # User → API
    ((1.5, 10), (1.5, 9.5)),
    # API → Intelligence
    ((2.5, 9), (3.5, 8.75)),
    # Intelligence → LLM
    ((6.5, 8.75), (7.5, 9)),
    # Intelligence → Strategies
    ((4.5, 7.5), (1, 6.4)),
    ((5, 7.5), (3, 6.4)),
    ((5.5, 7.5), (5, 6.4)),
    ((6, 7.5), (7, 6.4)),
    # Strategies → Storage
    ((1, 5.6), (1, 4.4)),
    ((5, 5.6), (5, 4.4)),
    ((7, 5.6), (8, 4.4)),
    # Storage → Monitoring
    ((1, 3.6), (2, 3)),
    ((5, 3.6), (4.75, 3)),
    ((8, 3.6), (7.5, 3))
]

for start, end in arrows:
    arrow = ConnectionPatch(start, end, "data", "data", 
                           arrowstyle="-|>", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="black", alpha=0.7)
    ax.add_patch(arrow)

# Légende des intentions
legend_box = FancyBboxPatch((0.5, 0.2), 4, 1.3, boxstyle="round,pad=0.1",
                           facecolor='lightgray', alpha=0.3, edgecolor='black')
ax.add_patch(legend_box)
ax.text(2.5, 1.3, 'Types d\'Intentions Supportées', fontsize=12, fontweight='bold', ha='center')

intentions = [
    'DIRECT_ANSWER: Salutations, questions générales',
    'RAG_NEEDED: Informations factuelles sur Polytech',
    'SYLLABUS_SPECIFIC_COURSE: Question sur un cours',
    'SYLLABUS_SPECIALITY_OVERVIEW: Tous les cours d\'une spé'
]

for i, intention in enumerate(intentions):
    ax.text(0.7, 1.1 - i*0.15, f'• {intention}', fontsize=9, ha='left', va='center')

# Statistiques de performance
stats_box = FancyBboxPatch((5.5, 0.2), 4, 1.3, boxstyle="round,pad=0.1",
                          facecolor='lightblue', alpha=0.3, edgecolor='black')
ax.add_patch(stats_box)
ax.text(7.5, 1.3, 'Métriques de Performance', fontsize=12, fontweight='bold', ha='center')

stats = [
    'Temps de réponse: ~2-3 secondes',
    'Précision d\'intention: >95%',
    'Coût par question: ~$0.02-0.05',
    'Documents récupérés: 8-12 par requête'
]

for i, stat in enumerate(stats):
    ax.text(5.7, 1.1 - i*0.15, f'• {stat}', fontsize=9, ha='left', va='center')

plt.tight_layout()
plt.savefig('/srv/partage/Stage-Chatbot-Polytech/docs/architecture_diagram.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Diagramme d'architecture généré: docs/architecture_diagram.png")

# Générer aussi un diagramme de flux
fig2, ax2 = plt.subplots(1, 1, figsize=(14, 10))
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.axis('off')

# Titre du flux
ax2.text(5, 9.5, 'Flux de Traitement des Requêtes', fontsize=18, fontweight='bold', ha='center')

# Étapes du flux
steps = [
    ('Question\nUtilisateur', 1, 8, colors['user']),
    ('Analyse\nd\'Intention', 3, 8, colors['intelligence']),
    ('Routage\nIntelligent', 5, 8, colors['intelligence']),
    ('Récupération\nDocuments', 7, 8, colors['retrieval']),
    ('Génération\nRéponse', 9, 8, colors['llm']),
    ('Logging &\nTracking', 5, 6, colors['monitoring']),
    ('Réponse\nUtilisateur', 5, 4, colors['user'])
]

for name, x, y, color in steps:
    step_box = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, boxstyle="round,pad=0.1",
                             facecolor=color, alpha=0.7, edgecolor='black')
    ax2.add_patch(step_box)
    ax2.text(x, y, name, fontsize=10, fontweight='bold', ha='center', va='center', color='white')

# Flèches du flux
flow_arrows = [
    ((1.6, 8), (2.4, 8)),
    ((3.6, 8), (4.4, 8)),
    ((5.6, 8), (6.4, 8)),
    ((7.6, 8), (8.4, 8)),
    ((9, 7.6), (5.6, 6.4)),
    ((5, 5.6), (5, 4.4))
]

for start, end in flow_arrows:
    arrow = ConnectionPatch(start, end, "data", "data", 
                           arrowstyle="-|>", shrinkA=5, shrinkB=5, 
                           mutation_scale=20, fc="black", alpha=0.7)
    ax2.add_patch(arrow)

# Détails des étapes
details = [
    ('1. Classification automatique\n   par LLM (gpt-4o-mini)', 3, 7.2),
    ('2. Choix de la stratégie\n   selon l\'intention', 5, 7.2),
    ('3. Filtrage par métadonnées\n   ou similarité sémantique', 7, 7.2),
    ('4. Prompt contextuel\n   + historique si nécessaire', 9, 7.2),
    ('5. Tokens, coûts, performance\n   + statistiques détaillées', 5, 5.2)
]

for detail, x, y in details:
    ax2.text(x, y, detail, fontsize=8, ha='center', va='top', 
            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('/srv/partage/Stage-Chatbot-Polytech/docs/flow_diagram.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
print("✅ Diagramme de flux généré: docs/flow_diagram.png")

plt.show()

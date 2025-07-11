# Intelligent RAG System for Polytech Sorbonne

## Description

Système RAG (Retrieval-Augmented Generation) intelligent pour le chatbot de Polytech Sorbonne. Ce système utilise un graphe LangGraph pour analyser l'intention des utilisateurs et router intelligemment vers différents types de traitement.

## Architecture

### Composants principaux

1. **State Management** (`state.py`)
   - Définition des états du graphe
   - Types d'intentions supportées
   - Structures de données

2. **Graph Nodes** (`nodes.py`)
   - `intent_analysis_node`: Analyse d'intention avec OpenAI (sortie JSON)
   - `direct_answer_node`: Réponses directes sans RAG
   - `document_retrieval_node`: Récupération intelligente de documents
   - `rag_generation_node`: Génération de réponses avec contexte

3. **Graph Builder** (`graph.py`)
   - Construction du graphe LangGraph
   - Routage conditionnel basé sur l'intention
   - Interface principale `invoke_intelligent_rag()`

4. **API Integration** (`api.py`)
   - Endpoints FastAPI
   - Modèles Pydantic pour les requêtes/réponses

5. **Testing & CLI** (`test_intelligent_rag.py`, `cli.py`)
   - Tests automatisés
   - Interface en ligne de commande
   - Mode interactif

## Types d'intentions

### DIRECT_ANSWER
- Salutations, remerciements
- Questions conversationnelles
- Pas de recherche documentaire

### RAG_NEEDED
- Questions factuelles sur Polytech
- Informations administratives
- Recherche documentaire standard

### SYLLABUS_TOC
- Questions sur les programmes
- Tables des matières
- Cours par spécialité
- Recherche spécialisée dans les syllabus

## Spécialités supportées

- **AGRAL**: Agroalimentaire
- **EISE**: Électronique et Informatique - Systèmes Embarqués
- **EI2I**: Électronique et Informatique - Informatique Industrielle
- **GM**: Génie Mécanique
- **MAIN**: Mathématiques Appliquées et Informatique
- **MTX**: Matériaux
- **ROB**: Robotique
- **ST**: Sciences de la Terre

## Utilisation

### Dans le code

```python
from intelligent_rag.graph import invoke_intelligent_rag

# Utilisation simple
result = invoke_intelligent_rag("Quels sont les cours en MAIN ?")

# Avec historique
result = invoke_intelligent_rag(
    "Et les débouchés ?", 
    chat_history=[
        {"role": "user", "content": "Parlez-moi de MAIN"},
        {"role": "assistant", "content": "MAIN est la spécialité..."}
    ]
)

print(result["answer"])
print(result["intent_analysis"]["intent"])
```

### CLI

```bash
# Mode interactif
python cli.py --mode interactive

# Mode batch
python cli.py --mode batch --questions "Bonjour" "Cours MAIN" "Associations"

# Tests automatiques
python cli.py --mode test
```

### API REST

```python
# Ajouter à votre FastAPI app
from intelligent_rag.api import router
app.include_router(router)
```

## Fonctionnalités avancées

### Analyse d'intention avec JSON
- Utilise OpenAI pour analyser l'intention
- Retour structuré en JSON avec confiance et spécialité
- Fallback en cas d'erreur de parsing

### Recherche documentaire intelligente
- Recherche spécialisée pour les syllabus/TOC
- Filtrage par tags et métadonnées
- Suppression automatique des doublons

### Gestion de l'historique
- Contexte conversationnel
- Références aux messages précédents
- Continuité dans la conversation

### Gestion d'erreurs robuste
- Fallback à chaque étape
- Logging détaillé
- Métriques de performance

## Tests

### Tests automatisés
```bash
python test_intelligent_rag.py
```

### Tests avec historique
- Simulation de conversations
- Vérification de la continuité
- Analyse des performances

## Intégration

### Avec l'API existante
```python
from intelligent_rag.api import router
app.include_router(router)
```

### Avec le système existant
```python
from intelligent_rag.graph import invoke_intelligent_rag

# Remplacement de l'ancien système
def chat_endpoint(question, history):
    return invoke_intelligent_rag(question, history)
```

## Configuration

### Variables d'environnement
- `OPENAI_API_KEY`: Clé API OpenAI
- Autres variables héritées du système existant

### Personnalisation
- Modifier `nodes.py` pour ajuster les prompts
- Adapter `state.py` pour de nouvelles intentions
- Étendre `graph.py` pour de nouveaux nœuds

## Monitoring

### Métriques disponibles
- Temps de traitement par nœud
- Taux de succès par intention
- Utilisation des différents chemins

### Logs
- Logs détaillés à chaque étape
- Erreurs avec stack traces
- Statistiques d'utilisation

## Évolutions futures

### Prévues
- Cache intelligent des résultats
- Apprentissage des préférences utilisateur
- Métriques de satisfaction

### Possibles
- Support multi-langues
- Intégration avec d'autres modèles
- Interface web dédiée

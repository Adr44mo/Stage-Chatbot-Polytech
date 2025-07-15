# 🧠 Intelligent RAG System for Polytech Sorbonne

## 📋 Description

Système RAG (Retrieval-Augmented Generation) intelligent pour le chatbot de Polytech Sorbonne. Ce système utilise un graphe LangGraph pour analyser l'intention des utilisateurs et router intelligemment vers différents types de traitement avec suivi complet des coûts et performances.

## 🏗️ Architecture

### Composants principaux

1. **State Management** (`state.py`)
   - Définition des états du graphe
   - Types d'intentions supportées (4 types)
   - Structures de données avec support historique

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
   - Endpoints FastAPI compatibles avec l'API existante
   - Modèles Pydantic pour les requêtes/réponses
   - Endpoints détaillés et simplifiés

5. **Token Tracking** (`token_tracker.py`)
   - Suivi détaillé des coûts OpenAI
   - Calcul automatique par opération
   - Détection dynamique du modèle (gpt-4o-mini)

6. **Advanced Logging** (`logger.py`)
   - Logs JSON structurés
   - Statistiques détaillées
   - Monitoring des performances

7. **Testing & CLI** (`cli.py`)
   - Tests automatisés
   - Interface en ligne de commande
   - Mode interactif

8. **Visualizations** (`visualizer.py`)
   - Génération de graphiques de performance
   - Statistiques visuelles

## 🎯 Types d'intentions

### DIRECT_ANSWER
- Salutations, remerciements
- Questions conversationnelles
- Pas de recherche documentaire

### RAG_NEEDED
- Questions factuelles sur Polytech
- Informations administratives, témoignages
- Recherche documentaire standard (documents généraux)

### SYLLABUS_SPECIFIC_COURSE
- Questions sur un cours spécifique
- Objectifs pédagogiques, programme détaillé
- Recherche ciblée dans les syllabus

### SYLLABUS_SPECIALITY_OVERVIEW
- Vue d'ensemble des cours d'une spécialité
- Tables des matières (TOC)
- Recherche par métadonnées (`metadata.type=toc`, `metadata.specialite=XXX`)

## 🎓 Spécialités à Polytech Sorbonne

- **AGRAL**: Agroalimentaire
- **EISE**: Électronique et Informatique - Systèmes Embarqués
- **EI2I**: Électronique et Informatique - Informatique Industrielle
- **GM**: Génie Mécanique
- **MAIN**: Mathématiques Appliquées et Informatique
- **MTX**: Matériaux
- **ROB**: Robotique
- **ST**: Sciences de la Terre

## 🚀 Utilisation

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
print(f"Coût: ${result['token_cost']['total_usd']:.4f}")
```

### API REST

#### Endpoints disponibles

```python
# Endpoint compatible avec l'API existante
POST /intelligent-rag/chat
{
  "prompt": "Quels sont les cours de robotique ?",
  "chat_history": []
}

# Endpoint détaillé avec toutes les informations
POST /intelligent-rag/chat_detailed
{
  "prompt": "Peux-tu me parler des témoignages d'étudiants ?",
  "chat_history": []
}

# Statistiques du système
GET /intelligent-rag/statistics
GET /intelligent-rag/statistics/daily?date=2025-01-11

# Santé du système
GET /intelligent-rag/health
```

#### Intégration avec l'API existante

```python
# Dans main.py
USE_INTELLIGENT_RAG = True  # Active le système intelligent

# L'endpoint /chat utilise automatiquement le système intelligent
POST /chat
{
  "prompt": "Question",
  "chat_history": []
}
```

### CLI

```bash
# Mode interactif
python -m Fastapi.backend.app.intelligent_rag.cli --mode interactive

# Mode batch
python -m Fastapi.backend.app.intelligent_rag.cli --mode batch --questions "Bonjour" "Cours MAIN" "Associations"

# Tests automatiques
python -m Fastapi.backend.app.intelligent_rag.cli --mode test
```

### CLI

```bash
# Mode interactif
python -m Fastapi.backend.app.intelligent_rag.cli --mode interactive

# Mode batch
python -m Fastapi.backend.app.intelligent_rag.cli --mode batch --questions "Bonjour" "Cours MAIN" "Associations"

# Tests automatiques
python -m Fastapi.backend.app.intelligent_rag.cli --mode test
```

## 💰 Suivi des Coûts et Performances

### Token Tracking
- **Coût par opération** : Analyse d'intention, génération de réponse
- **Modèle auto-détecté** : gpt-4o-mini (prix actualisés)
- **Tokens détaillés** : Input/Output pour chaque appel OpenAI
- **Coût total** : Calcul automatique par conversation

### Exemple de réponse avec coûts
```json
{
  "answer": "Réponse générée...",
  "token_cost": {
    "total_usd": 0.0234,
    "total_tokens": 156,
    "operations": [
      {
        "operation": "intent_analysis",
        "model": "gpt-4o-mini",
        "input_tokens": 12,
        "output_tokens": 0,
        "cost_usd": 0.0018
      },
      {
        "operation": "rag_generation", 
        "model": "gpt-4o-mini",
        "input_tokens": 120,
        "output_tokens": 24,
        "cost_usd": 0.0216
      }
    ]
  }
}
```

### Logs et Monitoring
- **Logs JSON** : Stockage dans `logs/responses/`
- **Statistiques** : Accès via API `/intelligent-rag/statistics`
- **Monitoring** : Performances, erreurs, coûts par jour
- **Visualisations** : Graphiques automatiques (`visualizer.py`)

## 🔧 Fonctionnalités avancées

### Analyse d'intention intelligente
- **Classification automatique** avec confiance > 95%
- **Détection de spécialité** et nom de cours
- **Gestion de l'historique** : Détermine si le contexte est nécessaire
- **Fallback robuste** en cas d'erreur

### Récupération de documents spécialisée

#### Pour les cours spécifiques
```python
# Recherche ciblée avec nom de cours
search_query = f"{course_name} {question}"
# Filtrage par tags: "cours", "syllabus"
```

#### Pour les vues d'ensemble de spécialités
```python
# Recherche directe par métadonnées
metadata_filter = {
    "metadata.type": "toc",
    "metadata.specialite": "ROB"  # Spécialité demandée
}
```

#### Pour les documents généraux
```python
# Récupération sans documents syllabus
# Recherche élargie avec mots-clés contextuels
```

### Gestion intelligente de l'historique
- **Détection automatique** : `needs_history` dans l'analyse d'intention
- **Contexte sélectif** : Utilise seulement les 3 derniers échanges
- **Continuité** : Références aux messages précédents


## 🔗 Intégration

### Avec l'API existante
```python
# Configuration dans main.py
USE_INTELLIGENT_RAG = True  # Active le système intelligent

# L'endpoint /chat utilise automatiquement le nouveau système
from intelligent_rag.api import router
app.include_router(router)
```

### Avec le système existant
```python
# Remplacement transparent
from intelligent_rag.graph import invoke_intelligent_rag

def chat_endpoint(question, history):
    result = invoke_intelligent_rag(question, history)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "cost": result["token_cost"]
    }
```

## ⚙️ Configuration

### Variables d'environnement
```bash
export OPENAI_API_KEY="your_openai_key"
export USE_INTELLIGENT_RAG=true
```

### Configuration du système
```python
# Dans main.py
USE_INTELLIGENT_RAG = True   # Système intelligent (recommandé)
USE_LANGGRAPH = True         # LangGraph RAG system 
# Si les deux sont False → RAG classique
```

### Personnalisation
- **Prompts** : Modifier `nodes.py` pour ajuster les prompts
- **Intentions** : Adapter `state.py` pour de nouvelles intentions
- **Workflow** : Étendre `graph.py` pour de nouveaux nœuds
- **Coûts** : Ajuster les prix dans `token_tracker.py`

## 📊 Monitoring et Statistiques

### Métriques disponibles
- **Temps de traitement** par nœud et opération
- **Taux de succès** par intention
- **Coûts détaillés** par conversation et par jour
- **Utilisation des différents chemins** de traitement

### Logs structurés
```bash
# Structure des logs
logs/
├── responses/          # Logs de conversations (JSON)
│   ├── 20250111_143052_abc123.json
│   └── ...
├── statistics/         # Stats journalières
│   ├── daily_20250111.json
│   └── ...
└── system.log         # Logs système
```

### Exemple de log de conversation
```json
{
  "session_id": "abc123",
  "timestamp": "2025-01-11T14:30:52",
  "request": {
    "question": "Quels sont les cours de ROB ?",
    "chat_history": []
  },
  "response": {
    "answer": "Voici les cours de Robotique...",
    "intent_analysis": {
      "intent": "SYLLABUS_SPECIALITY_OVERVIEW",
      "speciality": "ROB",
      "confidence": 0.95
    },
    "success": true
  },
  "performance": {
    "response_time_seconds": 2.34,
    "cost": {
      "total_usd": 0.0234,
      "operations": [...]
    }
  }
}
```

### Statistiques en temps réel
```bash
# Via API
GET /intelligent-rag/statistics

# Réponse
{
  "total_requests": 1234,
  "total_tokens": {"input": 45678, "output": 23456},
  "intents": {
    "RAG_NEEDED": 567,
    "SYLLABUS_SPECIALITY_OVERVIEW": 234,
    "SYLLABUS_SPECIFIC_COURSE": 123,
    "DIRECT_ANSWER": 89
  },
  "estimated_cost": {"total_usd": 12.34, "daily_usd": 2.45}
}
```

## 📈 Performance

### Métriques clés
- **Temps de réponse** : ~2-3 secondes
- **Précision d'intention** : >95%
- **Coût par question** : ~$0.002-0.005
- **Documents récupérés** : 8-12 par requête

### Optimisations implémentées
- **Batch processing** pour la vectorisation
- **Filtrage par métadonnées** pour les spécialités
- **Recherche directe** pour les documents TOC
- **Cache des sessions** pour le tracking des coûts

## 🚀 Évolutions futures

### 🔄 Prochaines améliorations
- **Cache intelligent** des résultats fréquents
- **Apprentissage des préférences** utilisateur
- **Métriques de satisfaction** avec feedback
- **Optimisation des coûts** avec modèles moins chers pour certaines tâches

### 🎯 Fonctionnalités possibles
- **Support multi-langues** (anglais, français)
- **Intégration avec d'autres modèles** (Mistral, Claude)
- **Interface web dédiée** pour les statistiques
- **API GraphQL** pour les requêtes complexes
- **Système de recommandations** basé sur l'historique

### 📊 Métriques avancées
- **A/B testing** entre différents prompts
- **Analyse de sentiment** des réponses
- **Détection de questions similaires** pour optimisation
- **Prédiction de l'intention** sans appel LLM

---

<div align="center">
  <sub>Construit avec ❤️ pour améliorer l'expérience étudiante à Polytech Sorbonne</sub>
</div>

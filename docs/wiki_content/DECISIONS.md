# 🤔 Décisions Architecturales

Ce document explique les décisions techniques importantes prises lors du développement du système RAG Polytech, avec les raisons derrière chaque choix.

## 📋 Table des Matières

1. [Framework Backend](#framework-backend)
2. [Framework Frontend](#framework-frontend)
3. [Base de Données](#base-de-données)
4. [Système RAG](#système-rag)
5. [Authentification](#authentification)
6. [Déploiement](#déploiement)
7. [Monitoring](#monitoring)

## 🔧 Framework Backend

### Décision : FastAPI
**Alternatives considérées :** Django, Flask, Express.js

**Pourquoi FastAPI ?**
- **Performance** : Support natif async/await, plus rapide que Django/Flask
- **Documentation** : Génération automatique OpenAPI/Swagger
- **Validation** : Pydantic pour validation de données robuste
- **Écosystème** : Intégration native avec LangChain
- **Développement** : Auto-reload en développement, debugging facilité

**Inconvénients acceptés :**
- Écosystème moins mature que Django
- Moins de packages tiers disponibles
- Courbe d'apprentissage pour l'async

```python
# Exemple : Validation automatique avec Pydantic
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    chat_history: List[ChatMessage] = Field(default=[], max_items=50)
    
# FastAPI génère automatiquement la documentation
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await process_chat(request)
```

## 🎨 Framework Frontend

### Décision : React + TypeScript
**Alternatives considérées :** Vue.js, Angular, Svelte

**Pourquoi React ?**
- **Écosystème** : Large communauté, nombreux packages
- **Performance** : Virtual DOM, optimisations React 19
- **Flexibilité** : Pas d'opinions fortes sur la structure
- **Hiring** : Plus facile de trouver des développeurs

**Pourquoi TypeScript ?**
- **Sécurité** : Détection d'erreurs à la compilation
- **IDE** : Meilleure auto-complétion et refactoring
- **Maintenabilité** : Code plus lisible et documenté
- **Intégration** : Excellent support avec React

```typescript
// Exemple : Typage strict des props
interface ChatProps {
  messages: Message[];
  onSendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
}

const ChatComponent: React.FC<ChatProps> = ({ messages, onSendMessage, isLoading }) => {
  // TypeScript détecte automatiquement les erreurs
  return <div>...</div>;
};
```

## 💾 Base de Données

### Décision : SQLite + ChromaDB
**Alternatives considérées :** PostgreSQL, MySQL, MongoDB

**Pourquoi SQLite ?**
- **Simplicité** : Pas de serveur à maintenir
- **Performance** : Excellent pour les lectures
- **Portabilité** : Fichier unique, facile à sauvegarder
- **Développement** : Pas de configuration complexe

**Pourquoi ChromaDB ?**
- **Spécialisé** : Optimisé pour les embeddings
- **Python-native** : Intégration directe avec LangChain
- **Simplicité** : Pas de configuration vectorielle complexe
- **Performance** : Recherche de similarité rapide

**Inconvénients acceptés :**
- SQLite : Pas de concurrence en écriture
- ChromaDB : Écosystème plus restreint que Pinecone

```python
# Exemple : Recherche vectorielle simple
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 12, "filter": {"specialite": "ROB"}}
)
docs = retriever.get_relevant_documents(query)
```

## 🧠 Système RAG

### Décision : LangGraph + Analyse d'Intention
**Alternatives considérées :** RAG simple, Retrieval seul, Fine-tuning

**Pourquoi LangGraph ?**
- **Modularité** : Workflow composable en nœuds
- **Debuggabilité** : Étapes clairement définies
- **Flexibilité** : Facilité d'ajout de nouvelles stratégies
- **Monitoring** : Suivi précis de chaque étape

**Pourquoi Analyse d'Intention ?**
- **Précision** : Stratégies adaptées au type de question
- **Performance** : Évite les recherches inutiles
- **Expérience** : Réponses plus pertinentes
- **Évolutivité** : Facilité d'ajout de nouveaux types

```python
# Exemple : Workflow modulaire
workflow = StateGraph(RagState)
workflow.add_node("analyze_intent", analyze_intent)
workflow.add_node("retrieve_documents", retrieve_documents)
workflow.add_node("generate_answer", generate_answer)

workflow.add_edge(START, "analyze_intent")
workflow.add_conditional_edges(
    "analyze_intent",
    route_based_on_intent,
    {
        "direct": "generate_answer",
        "rag_needed": "retrieve_documents"
    }
)
```

### Décision : OpenAI GPT-4o-mini
**Alternatives considérées :** GPT-4, Claude, LLaMA, Ollama local

**Pourquoi GPT-4o-mini ?**
- **Coût** : 60x moins cher que GPT-4
- **Performance** : Suffisante pour nos cas d'usage
- **Vitesse** : Réponses plus rapides
- **Disponibilité** : Pas de liste d'attente

**Inconvénients acceptés :**
- Capacité moindre que GPT-4 pour les tâches complexes
- Dépendance à OpenAI

## 🔐 Authentification

### Décision : JWT + reCAPTCHA
**Alternatives considérées :** Sessions, OAuth, Auth0

**Pourquoi JWT ?**
- **Stateless** : Pas de stockage serveur
- **Simplicité** : Facile à implémenter
- **Flexibilité** : Fonctionne avec SPA
- **Standards** : Largement supporté

**Pourquoi reCAPTCHA ?**
- **Efficacité** : Bloque efficacement les bots
- **Gratuit** : Pas de coûts supplémentaires
- **Intégration** : Facile à intégrer avec React

```python
# Exemple : Génération JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

## 🚀 Déploiement

### Décision : Docker + Nginx
**Alternatives considérées :** Kubernetes, Serverless, VM classique

**Pourquoi Docker ?**
- **Consistance** : Même environnement dev/prod
- **Portabilité** : Fonctionne partout
- **Simplicité** : Plus simple que Kubernetes
- **Ressources** : Moins gourmand qu'une VM

**Pourquoi Nginx ?**
- **Performance** : Excellent pour les fichiers statiques
- **Fiabilité** : Très stable en production
- **Flexibilité** : Proxy, SSL, compression
- **Monitoring** : Logs détaillés

```dockerfile
# Exemple : Multi-stage build
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## 📊 Monitoring

### Décision : Logs + Métriques Custom
**Alternatives considérées :** Prometheus, Grafana, ELK Stack

**Pourquoi Logs Custom ?**
- **Simplicité** : Pas d'infrastructure complexe
- **Coût** : Pas de services externes
- **Contrôle** : Métriques exactement comme on les veut
- **Débogage** : Accès direct aux données

**Pourquoi SQLite pour les métriques ?**
- **Cohérence** : Même base que l'application
- **Simplicité** : Pas de service supplémentaire
- **Requêtes** : SQL familier pour les analyses
- **Backup** : Inclus dans la sauvegarde principale

```python
# Exemple : Tracking personnalisé
@track_openai_call("intent_analysis")
def analyze_intent(state: RagState) -> RagState:
    # Le décorateur track automatiquement les tokens et coûts
    result = llm.invoke(prompt)
    return {"intent": result.content}
```

## 🔄 Évolutions Futures

### Décisions Reportées

**Microservices**
- **Pourquoi pas maintenant** : Complexité non justifiée
- **Quand** : Si > 10 développeurs ou besoins spécifiques
- **Comment** : Séparer RAG, Auth, Frontend

**Base de Données Distribuée**
- **Pourquoi pas maintenant** : SQLite suffisant
- **Quand** : Si > 1000 utilisateurs concurrents
- **Comment** : Migration vers PostgreSQL + Redis

**Cache Avancé**
- **Pourquoi pas maintenant** : Performance acceptable
- **Quand** : Si latence > 3 secondes
- **Comment** : Redis pour cache embeddings

### Décisions Techniques Controversées

**Pourquoi pas Pinecone ?**
- **Coût** : 70$/mois vs gratuit ChromaDB
- **Complexité** : Configuration + API management
- **Dépendance** : Vendor lock-in
- **Besoin** : Performance actuelle suffisante

**Pourquoi pas Next.js ?**
- **SSR** : Pas nécessaire pour une SPA
- **Complexité** : Vercel dependency
- **Équipe** : Plus familière avec React seul
- **Besoin** : CSR suffit pour le cas d'usage

**Pourquoi pas Kubernetes ?**
- **Ressources** : Trop gourmand pour un petit projet
- **Complexité** : Courbe d'apprentissage élevée
- **Besoin** : Docker Compose suffit
- **Équipe** : Pas d'expertise DevOps avancée

## 🎯 Métriques de Décision

### Critères Principaux

1. **Simplicité** : Privilégier la solution la plus simple
2. **Maintenabilité** : Code facile à modifier
3. **Performance** : Temps de réponse < 3s
4. **Coût** : Budget limité étudiant
5. **Apprentissage** : Technos connues de l'équipe

### Compromis Acceptés

**Performance vs Simplicité**
- SQLite au lieu de PostgreSQL
- Accepter quelques millisecondes de plus pour éviter la complexité

**Fonctionnalités vs Temps**
- RAG intelligent au lieu de fine-tuning
- Analyse d'intention au lieu de ML complexe

**Coût vs Performance**
- GPT-4o-mini au lieu de GPT-4
- ChromaDB au lieu de Pinecone

## 📚 Ressources & Références

### Documentation Consultée
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://langchain.readthedocs.io/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### Benchmarks Réalisés
- **FastAPI vs Django** : 2x plus rapide pour les API
- **ChromaDB vs Pinecone** : Performance similaire, coût 70x moins cher
- **GPT-4o-mini vs GPT-4** : Qualité acceptable, coût 60x moins cher

### Retours d'Expérience
- **Complexité** : LangGraph initialement déroutant mais payant
- **Performance** : SQLite surprenant en lecture
- **Développement** : TypeScript ralentit au début mais accélère après

---

Ces décisions peuvent évoluer selon les besoins futurs du projet. L'important est de documenter le raisonnement pour les futures équipes.

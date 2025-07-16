# 🏗️ Architecture du Système RAG Polytech

## 📋 Vue d'Ensemble

Le système RAG Polytech est conçu comme une architecture modulaire et évolutive, combinant intelligence artificielle et récupération de documents pour fournir des réponses contextuelles aux étudiants.

## 🎯 Décisions d'Architecture

### Pourquoi FastAPI ?
- **Performance** : Async/await natif pour haute concurrence
- **Documentation** : Génération automatique OpenAPI/Swagger
- **Validation** : Pydantic pour validation des données
- **Écosystème** : Intégration native avec LangChain

### Pourquoi React + TypeScript ?
- **Performance** : Virtual DOM et optimisations React 19
- **Sécurité** : Typage statique TypeScript
- **Écosystème** : Riche librairie de composants
- **Maintenance** : Code plus maintenable et lisible

### Pourquoi ChromaDB ?
- **Vectorisation** : Optimisé pour les embeddings
- **Performance** : Recherche de similarité rapide
- **Simplicité** : Pas de configuration complexe
- **Python-native** : Intégration directe avec LangChain

## 🏛️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Frontend                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    React App (Port 5173)                       ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              ││
│  │  │   Pages     │ │ Components  │ │   Hooks     │              ││
│  │  │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │              ││
│  │  │ │  Chat   │ │ │ │ChatBox  │ │ │ │useChat  │ │              ││
│  │  │ │  Admin  │ │ │ │Message  │ │ │ │useAPI   │ │              ││
│  │  │ │  Stats  │ │ │ │Sidebar  │ │ │ │useAuth  │ │              ││
│  │  │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │              ││
│  │  └─────────────┘ └─────────────┘ └─────────────┘              ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP/REST API
                                 │
┌─────────────────────────────────────────────────────────────────────┐
│                              Backend                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                   FastAPI App (Port 8000)                      ││
│  │                                                                 ││
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              ││
│  │  │   Routes    │ │ Intelligent │ │   Auth      │              ││
│  │  │ ┌─────────┐ │ │     RAG     │ │ ┌─────────┐ │              ││
│  │  │ │  Chat   │ │ │ ┌─────────┐ │ │ │  JWT    │ │              ││
│  │  │ │  Admin  │ │ │ │ Graph   │ │ │ │ reCAPT  │ │              ││
│  │  │ │  Stats  │ │ │ │ Nodes   │ │ │ │ Limiter │ │              ││
│  │  │ └─────────┘ │ │ │ State   │ │ │ └─────────┘ │              ││
│  │  └─────────────┘ │ └─────────┘ │ └─────────────┘              ││
│  │                  └─────────────┘                               ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                  │
│                                                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │  ChromaDB   │ │   SQLite    │ │   Redis     │ │   OpenAI    │  │
│  │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │  │
│  │ │Vectores │ │ │ │  Logs   │ │ │ │  Cache  │ │ │ │   GPT   │ │  │
│  │ │Embeddin │ │ │ │ Stats   │ │ │ │ Sessions│ │ │ │Embeddin │ │  │
│  │ │Document │ │ │ │  Auth   │ │ │ │ Limits  │ │ │ │  API    │ │  │
│  │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🧠 Système RAG Intelligent

### Workflow LangGraph

```python
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph RAG Workflow                          │
├─────────────────────────────────────────────────────────────────────┤
│  Input: Question + Chat History                                     │
│                           │                                         │
│  ┌─────────────────────────▼─────────────────────────┐              │
│  │  1. Intent Analysis                                │              │
│  │     ┌─────────────────────────────────────────────┐│              │
│  │     │ LLM Classification:                         ││              │
│  │     │ • DIRECT_ANSWER                            ││              │
│  │     │ • RAG_NEEDED                               ││              │
│  │     │ • SYLLABUS_SPECIFIC_COURSE                 ││              │
│  │     │ • SYLLABUS_SPECIALITY_OVERVIEW             ││              │
│  │     └─────────────────────────────────────────────┘│              │
│  └─────────────────────────┬─────────────────────────┘              │
│                           │                                         │
│  ┌─────────────────────────▼─────────────────────────┐              │
│  │  2. Routing Decision                               │              │
│  │     ┌─────────────────────────────────────────────┐│              │
│  │     │ if DIRECT_ANSWER → Direct Response          ││              │
│  │     │ if RAG_NEEDED → General RAG                 ││              │
│  │     │ if SYLLABUS_* → Specialized RAG             ││              │
│  │     └─────────────────────────────────────────────┘│              │
│  └─────────────────────────┬─────────────────────────┘              │
│                           │                                         │
│  ┌─────────────────────────▼─────────────────────────┐              │
│  │  3. Document Retrieval                             │              │
│  │     ┌─────────────────────────────────────────────┐│              │
│  │     │ ChromaDB Vector Search:                     ││              │
│  │     │ • Similarity search                         ││              │
│  │     │ • Metadata filtering                        ││              │
│  │     │ • Ranking & selection                       ││              │
│  │     └─────────────────────────────────────────────┘│              │
│  └─────────────────────────┬─────────────────────────┘              │
│                           │                                         │
│  ┌─────────────────────────▼─────────────────────────┐              │
│  │  4. Context Generation                             │              │
│  │     ┌─────────────────────────────────────────────┐│              │
│  │     │ LLM Generation:                             ││              │
│  │     │ • Context-aware response                    ││              │
│  │     │ • Source citation                           ││              │
│  │     │ • Structured output                         ││              │
│  │     └─────────────────────────────────────────────┘│              │
│  └─────────────────────────┬─────────────────────────┘              │
│                           │                                         │
│  ┌─────────────────────────▼─────────────────────────┐              │
│  │  5. Response + Logging                             │              │
│  │     ┌─────────────────────────────────────────────┐│              │
│  │     │ • Structured response                       ││              │
│  │     │ • Token tracking                            ││              │
│  │     │ • Performance metrics                       ││              │
│  │     │ • Database logging                          ││              │
│  │     └─────────────────────────────────────────────┘│              │
│  └─────────────────────────┬─────────────────────────┘              │
│                           │                                         │
│  Output: IntelligentRAGResponse                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Types d'Intentions

```python
class IntentType(Enum):
    DIRECT_ANSWER = "DIRECT_ANSWER"
    RAG_NEEDED = "RAG_NEEDED"
    SYLLABUS_SPECIFIC_COURSE = "SYLLABUS_SPECIFIC_COURSE"
    SYLLABUS_SPECIALITY_OVERVIEW = "SYLLABUS_SPECIALITY_OVERVIEW"

# Mapping vers stratégies
INTENT_TO_STRATEGY = {
    IntentType.DIRECT_ANSWER: "direct_response",
    IntentType.RAG_NEEDED: "general_rag",
    IntentType.SYLLABUS_SPECIFIC_COURSE: "course_specific_rag",
    IntentType.SYLLABUS_SPECIALITY_OVERVIEW: "speciality_overview_rag"
}
```

## 💾 Couche de Données

### Base de Données SQLite

```sql
-- Conversations
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    timestamp DATETIME,
    request_data TEXT,
    response_data TEXT,
    intent TEXT,
    success BOOLEAN,
    response_time REAL,
    total_tokens INTEGER,
    cost_usd REAL
);

-- Token Usage
CREATE TABLE token_usage (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp DATETIME,
    operation TEXT,
    model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd REAL
);

-- User Sessions
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    user_agent TEXT,
    ip_address TEXT,
    created_at DATETIME,
    last_activity DATETIME
);
```

### ChromaDB Structure

```python
# Collections
COLLECTIONS = {
    "polytech_docs": {
        "embedding_function": OpenAIEmbeddings(),
        "metadata_fields": [
            "source",
            "document_type",
            "specialite",
            "cours",
            "chunk_index"
        ]
    }
}

# Metadata Schema
METADATA_SCHEMA = {
    "source": str,          # "pdf_man", "data_sites"
    "document_type": str,   # "syllabus", "toc", "course", "testimonial"
    "specialite": str,      # "ROB", "GM", "EI2I", etc.
    "cours": str,           # "Algorithmique", "Robotique", etc.
    "chunk_index": int,     # Position dans le document
    "file_path": str,       # Chemin original
    "tags": List[str]       # Tags additionnels
}
```

## 🔧 Configuration & Déploiement

### Variables d'Environnement

```python
# Configuration centralisée
@dataclass
class Config:
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # RAG System
    use_intelligent_rag: bool = True
    use_langgraph: bool = True
    max_docs_retrieval: int = 12
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Database
    database_url: str = "sqlite:///./logs/rag_system.db"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Performance
    enable_caching: bool = True
    cache_ttl: int = 3600
    
    # Monitoring
    enable_monitoring: bool = True
    log_level: str = "INFO"
```

### Structure des Logs

```
logs/
├── rag_system.db          # Base de données principale
├── system.log             # Logs système
├── access.log             # Logs d'accès
├── error.log              # Logs d'erreurs
└── performance.log        # Métriques de performance
```

## 📡 API Design

### Endpoints Principaux

```python
# Chat Endpoints
POST /chat                              # Compatible legacy
POST /intelligent-rag/chat_intelligent  # RAG intelligent
GET  /intelligent-rag/health            # Health check

# Database & Analytics
GET  /intelligent-rag/database/statistics         # Stats globales
GET  /intelligent-rag/database/statistics/daily   # Stats journalières
GET  /intelligent-rag/database/conversations/recent  # Conversations récentes
GET  /intelligent-rag/database/metrics/performance  # Métriques performance

# Maintenance
POST /intelligent-rag/database/maintenance/cleanup  # Nettoyage
GET  /intelligent-rag/database/info                # Info DB
```

### Modèles de Données

```python
# Request Models
class ChatRequest(BaseModel):
    prompt: str
    chat_history: List[ChatMessage] = []

class IntelligentRAGRequest(BaseModel):
    question: str
    chat_history: List[ChatMessage] = []

# Response Models
class IntelligentRAGResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]
    sources: List[str]
    intent_analysis: Optional[Dict[str, Any]]
    processing_steps: List[str]
    success: bool
    error: Optional[str]
    response_time: float
    session_id: Optional[str]
    token_cost: Optional[Dict[str, Any]]
```

## 🔐 Sécurité

### Authentification & Autorisation

```python
# JWT Token Flow
┌─────────────────────────────────────────────────────────────────────┐
│  1. User Login                                                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ POST /auth/login                                            │ │
│     │ {username, password} → JWT Token                            │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                │                                    │
│  2. Token Verification                                              │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ Authorization: Bearer <token>                               │ │
│     │ → get_current_user() → User object                          │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                │                                    │
│  3. Role-Based Access                                               │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ Admin endpoints: get_current_admin()                        │ │
│     │ User endpoints: get_current_user()                          │ │
│     └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Protection CSRF & Rate Limiting

```python
# Rate Limiting
@limiter.limit("5/minute")
async def chat_endpoint():
    pass

# CORS Protection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input Validation
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    chat_history: List[ChatMessage] = Field(default=[], max_items=50)
```

## 📊 Monitoring & Observabilité

### Métriques Collectées

```python
# Performance Metrics
{
    "response_time": float,      # Temps de réponse (ms)
    "token_usage": {
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int
    },
    "cost_usd": float,          # Coût en USD
    "intent_accuracy": float,   # Précision d'intention
    "user_satisfaction": float  # Score satisfaction
}

# System Metrics
{
    "memory_usage": float,      # Utilisation mémoire
    "cpu_usage": float,         # Utilisation CPU
    "disk_usage": float,        # Utilisation disque
    "active_sessions": int,     # Sessions actives
    "error_rate": float        # Taux d'erreurs
}
```

### Logging Strategy

```python
# Structured Logging
logger.info(
    "RAG request processed",
    extra={
        "session_id": session_id,
        "intent": intent,
        "response_time": response_time,
        "tokens_used": total_tokens,
        "cost_usd": cost,
        "success": success
    }
)
```

## 🚀 Déploiement

### Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Production                                │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │   Nginx     │    │   FastAPI   │    │   React     │            │
│  │  (Proxy)    │◄──►│  (Backend)  │    │ (Frontend)  │            │
│  │   :80/:443  │    │   :8000     │    │   :5173     │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│                             │                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │   SQLite    │    │  ChromaDB   │    │   Redis     │            │
│  │   (Logs)    │    │ (Vectors)   │    │  (Cache)    │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

### Docker Configuration

```dockerfile
# Dockerfile.backend
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

## 🔄 Évolution & Maintenance

### Prochaines Améliorations

1. **Caching Avancé**
   - Cache des embeddings
   - Cache des réponses fréquentes
   - Cache distribué Redis

2. **Monitoring Avancé**
   - Métriques temps réel
   - Alertes automatiques
   - Dashboards Grafana

3. **Optimisations Performance**
   - Pagination des résultats
   - Compression des réponses
   - CDN pour le frontend

4. **Scalabilité**
   - Load balancing
   - Microservices
   - Database sharding

### Maintenance Régulière

```bash
# Nettoyage automatique
0 2 * * * /path/to/cleanup_old_logs.sh

# Backup base de données
0 3 * * * /path/to/backup_database.sh

# Monitoring santé
*/5 * * * * /path/to/health_check.sh
```

---

Cette architecture est conçue pour être **modulaire**, **évolutive** et **maintenable**. Chaque composant peut être modifié indépendamment, permettant une évolution progressive du système.

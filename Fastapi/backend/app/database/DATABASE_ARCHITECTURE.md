# Architecture de la Base de Données Unifiée

## Vue d'ensemble

Le système utilise une base de données SQLite unifiée qui combine :
- **Système d'authentification** (SQLModel)
- **Système de chat/conversations** (SQLModel) 
- **Système RAG intelligent** (SQLite natif)

## Diagramme des Relations

```mermaid
erDiagram
    %% Tables SQLModel (Auth + Chat)
    User {
        int id PK
        string username UK
        string hashed_password
        string role
    }
    
    Conversation {
        int id PK
        string session_id
        datetime created_at
    }
    
    Message {
        int id PK
        int conversation_id FK
        string role
        string content
        datetime timestamp
        string sources
    }
    
    %% Tables SQLite RAG
    rag_conversations {
        int id PK
        string session_id UK
        datetime timestamp
        string question
        string answer
        string chat_history
        string intent_analysis
        int context_docs_count
        int sources_count
        string processing_steps
        boolean success
        string error
        real response_time
        int user_input_tokens
        int final_output_tokens
        int intermediate_input_tokens
        int intermediate_output_tokens
        int total_input_tokens
        int total_output_tokens
        int grand_total_tokens
        real total_cost_usd
        datetime created_at
    }
    
    token_operations {
        int id PK
        string session_id FK
        string operation
        string model
        int input_tokens
        int output_tokens
        int total_tokens
        real cost_usd
        datetime timestamp
    }
    
    context_documents {
        int id PK
        string session_id FK
        string content_preview
        string metadata
        datetime created_at
    }
    
    global_statistics {
        int id PK
        string stat_name UK
        string stat_value
        datetime last_updated
    }
    
    %% Relations
    Conversation ||--o{ Message : "has many"
    rag_conversations ||--o{ token_operations : "has many"
    rag_conversations ||--o{ context_documents : "has many"
    
    %% Note: User n'a pas de relation directe avec Conversation
    %% car les conversations sont anonymes (session_id)
```

## Architecture des Fichiers

### 1. Tables SQLModel (créées par SQLAlchemy/SQLModel)

#### **Fichier : `app/database/models.py`**
- **Table `user`** : Authentification et autorisation
- **Note** : Gérée par SQLModel, utilise l'ORM

#### **Fichier : `app/chat_models.py`**
- **Table `conversation`** : Conversations anonymes
- **Table `message`** : Messages individuels
- **Relation** : `conversation.id` ← `message.conversation_id`

#### **Création via :**
```python
# app/database/database.py
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

### 2. Tables SQLite RAG (créées par SQL natif)

#### **Fichier : `app/database/database.py` (classe UnifiedDatabase)**
- **Table `rag_conversations`** : Conversations RAG détaillées
- **Table `token_operations`** : Opérations de tokens par session
- **Table `context_documents`** : Documents contextuels utilisés
- **Table `global_statistics`** : Statistiques globales

#### **Relations :**
- `rag_conversations.session_id` ← `token_operations.session_id`
- `rag_conversations.session_id` ← `context_documents.session_id`

#### **Création via :**
```python
# app/database/database.py
def _init_rag_database(self):
    # Crée les tables avec CREATE TABLE IF NOT EXISTS
```

## Fichiers Responsables de Chaque Table

| Table | Fichier | Méthode | Type |
|-------|---------|---------|------|
| `user` | `app/database/models.py` | SQLModel | ORM |
| `conversation` | `app/chat_models.py` | SQLModel | ORM |
| `message` | `app/chat_models.py` | SQLModel | ORM |
| `rag_conversations` | `app/database/database.py` | `_init_rag_database()` | SQL natif |
| `token_operations` | `app/database/database.py` | `_init_rag_database()` | SQL natif |
| `context_documents` | `app/database/database.py` | `_init_rag_database()` | SQL natif |
| `global_statistics` | `app/database/database.py` | `_init_rag_database()` | SQL natif |

## Que se passe-t-il si je supprime toute la DB ?

### **Suppression du fichier `database.db`**

```bash
rm /srv/partage/Stage-Chatbot-Polytech/Fastapi/backend/app/database/database.db
```

### **Conséquences :**

1. **Perte de données :**
   - ❌ Tous les comptes utilisateurs (admins)
   - ❌ Tout l'historique des conversations
   - ❌ Tous les messages sauvegardés
   - ❌ Toutes les statistiques RAG
   - ❌ Toutes les données de performance

2. **Au prochain démarrage :**
   - ✅ Le fichier `database.db` sera recréé automatiquement
   - ✅ Toutes les tables seront recréées (vides)
   - ❌ **Pas de compte admin** → vous ne pourrez plus vous connecter
   - ✅ Le système continuera à fonctionner pour les utilisateurs anonymes

### **Récupération après suppression :**

1. **Recréer un compte admin :**
   ```bash
   cd /srv/partage/Stage-Chatbot-Polytech/Fastapi/backend/app/database
   python create_admin.py
   ```

2. **Ou via Python :**
   ```python
   from app.database.create_admin import create_admin
   create_admin()
   ```

### **Processus de re-initialisation automatique :**

1. **Au démarrage de FastAPI :**
   ```python
   @app.on_event("startup")
   def on_startup():
       create_db_and_tables()  # Crée les tables SQLModel
       # unified_database s'initialise automatiquement
   ```

2. **Lors de la première utilisation :**
   ```python
   # UnifiedDatabase.__init__() appelé automatiquement
   unified_database = UnifiedDatabase()
   # → Crée les tables RAG automatiquement
   ```

## Sauvegardes Recommandées

### **Sauvegarde manuelle :**
```bash
cp /srv/partage/Stage-Chatbot-Polytech/Fastapi/backend/app/database/database.db /backup/database_$(date +%Y%m%d_%H%M%S).db
```

### **Sauvegarde automatique :**
```python
# Ajouter dans le code
def backup_database():
    import shutil
    from datetime import datetime
    
    source = "/srv/partage/Stage-Chatbot-Polytech/Fastapi/backend/app/database/database.db"
    backup = f"/backup/database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(source, backup)
```

## Deux Systèmes en Parallèle

**Important :** Le système actuel maintient deux systèmes de base de données :

1. **SQLModel** (conversations normales) : `conversation` + `message`
2. **SQLite RAG** (conversations intelligentes) : `rag_conversations` + tables liées

Cela permet une transition en douceur et la coexistence des deux systèmes.

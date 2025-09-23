<div align="center">

# Polytech Sorbonne - Chatbot RAG Intelligent

> **Un système de chatbot intelligent pour les étudiants de Polytech Sorbonne, propulsé par l'IA et la récupération de documents (RAG)**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.1-blue.svg)](https://react.dev)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Latest-purple.svg)](https://chromadb.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://sqlite.org)

![Polytech Chatbot Demo](docs_info/chat.png)

</div>

---

## Aperçu

**Chatbot RAG intelligent** utilisant l'IA pour fournir des réponses précises à toute personne souhaitant obtenir des informations sur Polytech Sorbonne : futurs étudiants (lycéens), parents, élèves actuels ou toute personne intéressée. Le système analyse automatiquement l'intention des questions et oriente les requêtes vers les meilleures stratégies de récupération.

## Fonctionnalités Clés

- **Analyse d'intention intelligente** - Classification automatique des questions
- **Routage adaptatif** - Stratégies de récupération optimisées
- **Monitoring avancé** - Tracking des coûts et performances
- **Sécurité intégrée** - Rate limiting et authentification

## Installation

Pour l’installation et le déploiement détaillé, voir le guide : [DEPLOYMENT.md](./DEPLOYMENT.md)

## Architecture

```mermaid
flowchart TD
    %% Utilisateur
    USER[👤 Utilisateur]
    
    %% Frontend
    subgraph FRONTEND[🖥️ Frontend - React]
        CHAT[💬 Interface Chat]
        ADMIN[⚙️ Administration]
        STATS[📊 Statistiques]
        SOURCES_UI[📁 Gestion Sources]
        SCRAPING_UI[🔍 Interface Scraping]
    end
    
    %% Backend API
    subgraph BACKEND[🚀 Backend - FastAPI]
        API[🌐 API Endpoints]
        RAG_SYSTEM[🧠 Système RAG Intelligent]
        INTENT[🎯 Analyse d'Intention]
        ROUTER[🔀 Routage Intelligent]
        
        subgraph RAG_STRATEGIES[💡 Stratégies RAG]
            RAG_GENERAL[📚 RAG Général<br/>Témoignages]
            RAG_SYLLABUS[📖 Cours Spécifique<br/>Syllabus]
            RAG_TOC[📋 Vue d'Ensemble<br/>TOC]
            DIRECT[💭 Réponse Directe]
        end
        
        LLM[🤖 OpenAI GPT-4o-mini]
        MONITORING[📈 Monitoring & Logs]
    end
    
    %% Gestion des Sources
    subgraph SOURCES[📂 Gestion des Sources]
        SCRAPING[🕷️ Scraping Web]
        PDF_HANDLER[📄 Traitement PDF]
        DOC_VALIDATION[✅ Validation Documents]
        VECTORIZATION[🔢 Vectorisation]
        EMBEDDINGS[🎯 Génération Embeddings]
        CORPUS_MGMT[📦 Gestion Corpus]
    end
    
    %% Stockage
    subgraph STORAGE[💾 Stockage]
        CHROMADB[(🔍 ChromaDB<br/>Embeddings)]
        SQLITE[(📊 SQLite<br/>Logs & Stats)]
        FILES[(📁 Fichiers<br/>PDF & JSON)]
    end
    
    %% Connexions principales
    USER --> FRONTEND
    FRONTEND --> BACKEND
    BACKEND --> SOURCES
    SOURCES --> STORAGE
    
    %% Connexions détaillées Frontend
    CHAT --> API
    ADMIN --> API
    STATS --> MONITORING
    SOURCES_UI --> SCRAPING
    SCRAPING_UI --> SCRAPING
    
    %% Connexions Backend
    API --> RAG_SYSTEM
    RAG_SYSTEM --> INTENT
    INTENT --> ROUTER
    ROUTER --> RAG_STRATEGIES
    RAG_STRATEGIES --> LLM
    RAG_STRATEGIES --> STORAGE
    LLM --> MONITORING
    
    %% Connexions Sources
    SCRAPING --> DOC_VALIDATION
    PDF_HANDLER --> DOC_VALIDATION
    DOC_VALIDATION --> VECTORIZATION
    VECTORIZATION --> EMBEDDINGS
    EMBEDDINGS --> CORPUS_MGMT
    CORPUS_MGMT --> CHROMADB
    
    %% Connexions Stockage
    MONITORING --> SQLITE
    CORPUS_MGMT --> FILES
    
    %% Styles
    classDef frontend fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff
    classDef backend fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff
    classDef sources fill:#f39c12,stroke:#e67e22,stroke-width:2px,color:#fff
    classDef storage fill:#34495e,stroke:#2c3e50,stroke-width:2px,color:#fff
    classDef rag fill:#9b59b6,stroke:#8e44ad,stroke-width:2px,color:#fff
    
    class FRONTEND,CHAT,ADMIN,STATS,SOURCES_UI,SCRAPING_UI frontend
    class BACKEND,API,RAG_SYSTEM,INTENT,ROUTER,LLM,MONITORING backend
    class RAG_GENERAL,RAG_SYLLABUS,RAG_TOC,DIRECT rag
    class SOURCES,SCRAPING,PDF_HANDLER,DOC_VALIDATION,VECTORIZATION,EMBEDDINGS,CORPUS_MGMT sources
    class STORAGE,CHROMADB,SQLITE,FILES storage
```

## Stack Technique

**Backend** : FastAPI • LangChain • ChromaDB • SQLite • OpenAI • Redis  
**Frontend** : React 19 • TypeScript • Vite  
**Infrastructure** : Nginx • Python 3.12

## Documentation Complète

### 📖 Guide Principal
- **[📚 Wiki du Projet](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki)** - Documentation complète
- **[🚀 Guide d'Installation](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Installation)** - Setup détaillé
- **[🔧 Configuration](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Configuration)** - Paramètres avancés

### Développement
- **[🏗️ Architecture](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Architecture)** - Structure technique

### Utilisation
- **[👤 Guide Utilisateur](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Guide-Utilisateur)** - Manuel utilisateur
- **[🌐 API Reference](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/API-Reference)** - Documentation API


## 📄 Licence

Ce projet est sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

## 👥 Équipe

- **Développeur** : [ilonaged](https://github.com/ilonaged) [CassandraMartin03](https://github.com/CassandraMartin03) [Adr44mo](https://github.com/Adr44mo)
- **Institution** : [Polytech Sorbonne](https://www.polytech.sorbonne-universite.fr/), [LIMICS](https://www.limics.fr/)
---

<div align="center">
  <sub>Développé avec ❤️ pour les étudiants de Polytech Sorbonne</sub>
  <br>
  <sub>Propulsé par OpenAI, LangChain, et l'intelligence artificielle</sub>
</div>

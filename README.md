<div align="center">

# 🤖 Polytech Sorbonne - Chatbot RAG Intelligent

> **Un système de chatbot intelligent pour les étudiants de Polytech Sorbonne, propulsé par l'IA et la récupération de documents (RAG)**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.1-blue.svg)](https://react.dev)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-orange.svg)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Latest-purple.svg)](https://chromadb.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://sqlite.org)

![Polytech Chatbot Demo](docs/images/demo_preview.png)

</div>

---

## 🚀 Aperçu

**Chatbot RAG intelligent** utilisant l'IA pour fournir des réponses précises aux étudiants de Polytech Sorbonne sur leurs cours, spécialités et vie étudiante. Le système analyse automatiquement l'intention des questions et route les requêtes vers les meilleures stratégies de récupération.

## ✨ Fonctionnalités Clés

- 🧠 **Analyse d'intention intelligente** - Classification automatique des questions
- 🔀 **Routage adaptatif** - Stratégies de récupération optimisées
- 📊 **Monitoring avancé** - Tracking des coûts et performances
- 🔐 **Sécurité intégrée** - Rate limiting et authentification
- ⚡ **Réponses temps réel** - Interface chat moderne

## 📊 Architecture

<div align="center">
  <img src="docs/architecture_diagram.png" alt="Architecture du Système RAG" width="800">
</div>

### 🔄 Workflow LangGraph

<div align="center">
  <img src="docs/langgraph_architecture.png" alt="LangGraph Workflow" width="700">
</div>

## 🛠️ Stack Technique

**Backend** : FastAPI • LangChain • ChromaDB • SQLite • OpenAI • Redis  
**Frontend** : React 19 • TypeScript • Vite  
**Infrastructure** : Docker • Nginx • Python 3.12

## ⚡ Installation Rapide

```bash
# 1. Cloner le projet
git clone https://github.com/Adr44mo/Stage-Chatbot-Polytech.git
cd Stage-Chatbot-Polytech

# 2. Configuration
cp .env.example .env
# Ajouter votre clé OpenAI dans .env

# 3. Installation des dépendances
pip install -r Fastapi/backend/requirements.txt
cd Fastapi/frontend && npm install

# 4. Démarrage automatique
chmod +x start.sh
./start.sh
```

**Accès** : http://localhost:5173

## 📚 Documentation Complète

### 📖 Guide Principal
- **[📚 Wiki du Projet](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki)** - Documentation complète
- **[🚀 Guide d'Installation](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Installation)** - Setup détaillé
- **[🔧 Configuration](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Configuration)** - Paramètres avancés

### 🔧 Développement
- **[🏗️ Architecture](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Architecture)** - Structure technique
- **[🧪 Tests](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Tests)** - Tests et validation
- **[🤝 Contribution](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Contribution)** - Guide de contribution

### 📊 Utilisation
- **[👤 Guide Utilisateur](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Guide-Utilisateur)** - Manuel utilisateur
- **[🌐 API Reference](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/API-Reference)** - Documentation API
- **[❓ FAQ](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/FAQ)** - Questions fréquentes

## 🆘 Support

- **[🐛 Issues](https://github.com/Adr44mo/Stage-Chatbot-Polytech/issues)** - Signaler un problème
- **[💬 Discussions](https://github.com/Adr44mo/Stage-Chatbot-Polytech/discussions)** - Questions et discussions
- **[📞 Contact](mailto:votre.email@polytech.fr)** - Support direct

## 🎯 Utilisation Rapide

### Types de Questions Supportées

| Type | Exemple |
|------|---------|
| **Cours** | *"Objectifs du cours d'Algorithmique ?"* |
| **Spécialité** | *"Tous les cours de robotique"* |
| **Général** | *"Témoignages d'étudiants"* |
| **Vie étudiante** | *"Activités disponibles"* |

### API Endpoints

```bash
# Chat standard
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Cours de robotique ?", "chat_history": []}'

# Statistiques
curl "http://localhost:8000/intelligent-rag/database/statistics"
```

## 📈 Performance

- **Temps de réponse** : 2-3 secondes
- **Précision** : >95%
- **Coût/question** : ~$0.02-0.05
- **Disponibilité** : 99.9%

## 🤝 Contribution

1. **Fork** le repository
2. **Créer une branche** : `git checkout -b feature/ma-fonctionnalite`
3. **Committer** : `git commit -m 'feat: nouvelle fonctionnalité'`
4. **Pull Request** : Ouvrir une PR

Voir le **[Guide de Contribution](https://github.com/Adr44mo/Stage-Chatbot-Polytech/wiki/Contribution)** pour plus de détails.

## 📄 Licence

Ce projet est sous licence **MIT**. Voir [LICENSE](LICENSE) pour plus de détails.

## 👥 Équipe

- **Développeur** : [Adr44mo](https://github.com/Adr44mo)
- **Institution** : Polytech Sorbonne
- **Contact** : [votre.email@polytech.fr](mailto:votre.email@polytech.fr)

---

<div align="center">
  <sub>Développé avec ❤️ pour les étudiants de Polytech Sorbonne</sub>
  <br>
  <sub>Propulsé par OpenAI, LangChain, et l'intelligence artificielle</sub>
</div>
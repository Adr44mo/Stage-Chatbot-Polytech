# 📚 Migration vers GitHub Wiki

Ce dossier contient tous les fichiers de documentation qui doivent être migrés vers le GitHub Wiki.

## 📋 Plan de Migration

### 1. Pages Wiki à Créer

| Fichier Source | Page Wiki | Description |
|----------------|-----------|-------------|
| `ARCHITECTURE.md` | `Architecture` | Structure technique du système |
| `CONTRIBUTING.md` | `Contribution` | Guide de contribution |
| `CHANGELOG.md` | `Changelog` | Historique des versions |
| `DECISIONS.md` | `Decisions` | Décisions techniques |
| `DEPLOYMENT.md` | `Deploiement` | Guide de déploiement |
| `DOCUMENTATION_REPORT.md` | `Documentation-Report` | Rapport de documentation |

### 2. Pages Additionnelles à Créer

- **`Home.md`** - Page d'accueil du Wiki
- **`Installation.md`** - Guide d'installation détaillé
- **`Configuration.md`** - Configuration avancée
- **`Guide-Utilisateur.md`** - Manuel utilisateur
- **`API-Reference.md`** - Documentation API
- **`FAQ.md`** - Questions fréquentes
- **`Troubleshooting.md`** - Résolution de problèmes
- **`Tests.md`** - Tests et validation
- **`Monitoring.md`** - Surveillance système
- **`Securite.md`** - Sécurité
- **`Maintenance.md`** - Maintenance
- **`Backup.md`** - Sauvegarde
- **`Contact.md`** - Contact et support

### 3. Sidebar Recommandée

```markdown
# 🤖 Polytech Chatbot

## 🚀 Démarrage
- [🏠 Accueil](Home)
- [⚡ Installation](Installation)
- [🔧 Configuration](Configuration)
- [🎯 Premiers Pas](Premiers-Pas)

## 📖 Documentation
- [🏗️ Architecture](Architecture)
- [🔀 Système RAG](Systeme-RAG)
- [🌐 API Reference](API-Reference)
- [📊 Base de Données](Base-de-Donnees)

## 💻 Développement
- [🛠️ Setup Dev](Setup-Developpement)
- [🧪 Tests](Tests)
- [🔄 Contribution](Contribution)
- [📦 Déploiement](Deploiement)

## 🎯 Utilisation
- [👤 Guide Utilisateur](Guide-Utilisateur)
- [🔍 Types de Questions](Types-Questions)
- [📈 Analytics](Analytics)
- [⚙️ Configuration Avancée](Configuration-Avancee)

## 🔧 Administration
- [📊 Monitoring](Monitoring)
- [🔒 Sécurité](Securite)
- [🔄 Maintenance](Maintenance)
- [💾 Backup](Backup)

## 🆘 Support
- [❓ FAQ](FAQ)
- [🐛 Troubleshooting](Troubleshooting)
- [📋 Changelog](Changelog)
- [📞 Contact](Contact)

---
🔗 [Repository Principal](https://github.com/Adr44mo/Stage-Chatbot-Polytech)
```

### 4. Étapes de Migration

1. **Activer le Wiki** sur GitHub
2. **Créer la page `_Sidebar.md`** avec le contenu ci-dessus
3. **Créer la page `Home.md`** comme page d'accueil
4. **Copier-coller** le contenu des fichiers dans les pages correspondantes
5. **Adapter le formatage** si nécessaire
6. **Créer les pages additionnelles** listées ci-dessus
7. **Tester tous les liens** internes

### 5. Pages d'Exemple

#### Home.md
```markdown
# 🏠 Accueil - Polytech Chatbot Wiki

Bienvenue dans la documentation complète du **Chatbot RAG Intelligent** de Polytech Sorbonne.

## 🚀 Démarrage Rapide

- [⚡ Installation](Installation) - Installer et configurer le système
- [🔧 Configuration](Configuration) - Paramètres et variables d'environnement
- [🎯 Premiers Pas](Premiers-Pas) - Utiliser le chatbot

## 📖 Documentation Technique

- [🏗️ Architecture](Architecture) - Structure du système
- [🌐 API Reference](API-Reference) - Documentation des endpoints
- [🧪 Tests](Tests) - Tests et validation

## 🆘 Besoin d'Aide ?

- [❓ FAQ](FAQ) - Questions fréquentes
- [🐛 Troubleshooting](Troubleshooting) - Résolution de problèmes
- [📞 Contact](Contact) - Support
```

#### Installation.md
```markdown
# ⚡ Installation - Guide Complet

## 📋 Prérequis

- Python 3.12+
- Node.js 18+
- Git
- OpenAI API Key

## 🔧 Installation Étape par Étape

### 1. Cloner le Repository
[Contenu détaillé...]

### 2. Configuration
[Contenu détaillé...]

### 3. Installation des Dépendances
[Contenu détaillé...]

### 4. Démarrage
[Contenu détaillé...]
```

## 📝 Instructions de Copie

1. **Aller sur GitHub** : https://github.com/Adr44mo/Stage-Chatbot-Polytech
2. **Activer le Wiki** : Settings → Features → Wiki
3. **Créer les pages** une par une
4. **Copier-coller** le contenu des fichiers markdown
5. **Adapter le formatage** si nécessaire

## 🔄 Après Migration

Une fois la migration terminée, vous pouvez :
- Supprimer ce dossier `docs/wiki_content/`
- Garder uniquement le README épuré
- Mettre à jour les liens dans le README si nécessaire

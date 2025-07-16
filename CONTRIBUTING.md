# 🤝 Guide de Contribution

Merci de votre intérêt pour contribuer au projet **Polytech Sorbonne Chatbot RAG** ! Ce guide vous aidera à comprendre comment contribuer efficacement.

## 📋 Table des Matières

1. [Code de Conduite](#code-de-conduite)
2. [Types de Contributions](#types-de-contributions)
3. [Environnement de Développement](#environnement-de-développement)
4. [Workflow de Contribution](#workflow-de-contribution)
5. [Standards de Code](#standards-de-code)
6. [Tests](#tests)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)

## 🤖 Code de Conduite

Ce projet adhère au [Code de Conduite Contributor Covenant](https://www.contributor-covenant.org/). En participant, vous acceptez de respecter ce code.

## 🎯 Types de Contributions

### 🐛 Correction de Bugs
- Reproduction et documentation des bugs
- Correction avec tests appropriés
- Amélioration de la robustesse

### ✨ Nouvelles Fonctionnalités
- Analyse d'intention améliorée
- Nouveaux types de documents
- Optimisations de performance
- Nouvelles métriques de monitoring

### 📚 Documentation
- Amélioration du README
- Documentation API
- Guides d'utilisation
- Tutoriels et exemples

### 🔧 Optimisations
- Performance backend/frontend
- Réduction des coûts tokens
- Amélioration UX

## 🛠️ Environnement de Développement

### Prérequis
- Python 3.12+
- Node.js 18+
- Redis (optionnel)
- Git

### Installation

```bash
# 1. Fork et cloner
git clone https://github.com/votre-username/Stage-Chatbot-Polytech.git
cd Stage-Chatbot-Polytech

# 2. Créer une branche
git checkout -b feature/ma-fonctionnalite

# 3. Installer les dépendances
cd Fastapi/backend
pip install -r requirements.txt

cd ../frontend
npm install

# 4. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos valeurs
```

### Lancement en Mode Développement

```bash
# Backend avec hot reload
cd Fastapi/backend
uvicorn main:app --reload --port 8000

# Frontend avec hot reload
cd Fastapi/frontend
npm run dev
```

## 🔄 Workflow de Contribution

### 1. Préparation
```bash
# Synchroniser avec main
git checkout main
git pull upstream main

# Créer une branche feature
git checkout -b feature/nom-descriptif
```

### 2. Développement
```bash
# Développer la fonctionnalité
# Commiter régulièrement
git add .
git commit -m "feat: description claire"
```

### 3. Tests
```bash
# Tests backend
cd Fastapi/backend
python -m pytest tests/

# Tests frontend
cd Fastapi/frontend
npm test
```

### 4. Soumission
```bash
# Push de la branche
git push origin feature/nom-descriptif

# Créer une Pull Request sur GitHub
```

## 📝 Standards de Code

### Backend (Python)

#### Style de Code
- **PEP 8** : Style guide officiel Python
- **Black** : Formatage automatique
- **isort** : Tri des imports
- **flake8** : Linting

```bash
# Formatage
black .
isort .

# Linting
flake8 .
```

#### Structure des Fichiers
```python
"""
Module docstring décrivant le but du module
"""

# Imports standard
import os
import sys

# Imports tiers
from fastapi import FastAPI
from langchain import LLMChain

# Imports locaux
from .models import ChatRequest
from .utils import logger

# Constants
MAX_TOKENS = 1000

# Classes et fonctions
class MyClass:
    """Docstring décrivant la classe"""
    
    def __init__(self):
        """Docstring du constructeur"""
        pass
    
    def method(self, param: str) -> str:
        """
        Docstring décrivant la méthode
        
        Args:
            param: Description du paramètre
            
        Returns:
            Description du retour
        """
        return param
```

### Frontend (TypeScript/React)

#### Structure des Composants
```typescript
// imports
import React, { useState, useEffect } from 'react';

// types
interface Props {
  title: string;
  onSubmit: (value: string) => void;
}

// component
export const MyComponent: React.FC<Props> = ({ title, onSubmit }) => {
  const [value, setValue] = useState<string>('');

  useEffect(() => {
    // effet
  }, []);

  const handleSubmit = () => {
    onSubmit(value);
  };

  return (
    <div>
      <h1>{title}</h1>
      {/* JSX */}
    </div>
  );
};
```

#### Linting
```bash
# ESLint
npm run lint

# Prettier
npm run format
```

### Conventions de Nommage

#### Python
```python
# Variables et fonctions : snake_case
my_variable = "value"
def my_function():
    pass

# Classes : PascalCase
class MyClass:
    pass

# Constantes : UPPER_CASE
MAX_RETRY_COUNT = 3

# Privé : _prefixe
def _private_function():
    pass
```

#### TypeScript
```typescript
// Variables et fonctions : camelCase
const myVariable = "value";
const myFunction = () => {};

// Classes et interfaces : PascalCase
class MyClass {}
interface MyInterface {}

// Constantes : UPPER_CASE
const MAX_RETRY_COUNT = 3;

// Composants : PascalCase
const MyComponent = () => {};
```

## 🧪 Tests

### Backend Tests

```bash
# Lancer tous les tests
python -m pytest

# Tests avec coverage
python -m pytest --cov=app

# Tests spécifiques
python -m pytest tests/test_rag_system.py -v
```

#### Structure des Tests
```python
# tests/test_example.py
import pytest
from app.intelligent_rag.nodes import analyze_intent

class TestIntentAnalysis:
    """Tests pour l'analyse d'intention"""
    
    def test_direct_answer_intent(self):
        """Test détection intention directe"""
        result = analyze_intent("Bonjour")
        assert result["intent"] == "DIRECT_ANSWER"
    
    def test_rag_needed_intent(self):
        """Test détection intention RAG"""
        result = analyze_intent("Parle-moi des témoignages")
        assert result["intent"] == "RAG_NEEDED"
    
    @pytest.mark.parametrize("question,expected", [
        ("Salut", "DIRECT_ANSWER"),
        ("Cours de robotique", "SYLLABUS_SPECIFIC_COURSE"),
    ])
    def test_intent_classification(self, question, expected):
        """Test classification d'intentions"""
        result = analyze_intent(question)
        assert result["intent"] == expected
```

### Frontend Tests

```bash
# Tests unitaires
npm test

# Tests avec coverage
npm run test:coverage

# Tests E2E
npm run test:e2e
```

## 📚 Documentation

### Docstrings Python
```python
def analyze_intent(question: str) -> Dict[str, Any]:
    """
    Analyse l'intention d'une question utilisateur.
    
    Cette fonction utilise un modèle LLM pour classifier
    l'intention derrière une question posée par l'utilisateur.
    
    Args:
        question: La question à analyser
        
    Returns:
        Dict contenant:
            - intent: Type d'intention détectée
            - confidence: Score de confiance (0-1)
            - reasoning: Explication du raisonnement
            
    Raises:
        ValueError: Si la question est vide
        OpenAIError: Si l'API OpenAI est indisponible
        
    Example:
        >>> analyze_intent("Bonjour")
        {
            "intent": "DIRECT_ANSWER",
            "confidence": 0.95,
            "reasoning": "Simple greeting"
        }
    """
```

### Commentaires JSDoc
```typescript
/**
 * Composant pour afficher une conversation de chat
 * 
 * @param messages - Liste des messages à afficher
 * @param onSendMessage - Callback appelé lors de l'envoi d'un message
 * @param isLoading - Indique si une réponse est en cours
 * 
 * @example
 * <ChatComponent
 *   messages={messages}
 *   onSendMessage={handleSend}
 *   isLoading={false}
 * />
 */
```

## 🔍 Pull Request Process

### Checklist PR

- [ ] **Code** : Respecte les standards de style
- [ ] **Tests** : Nouveaux tests pour les nouvelles fonctionnalités
- [ ] **Documentation** : Mise à jour si nécessaire
- [ ] **Performance** : Pas de régression notable
- [ ] **Sécurité** : Pas de vulnérabilités introduites
- [ ] **Breaking Changes** : Documentées si applicables

### Template PR

```markdown
## Description
Brève description des changements

## Type de changement
- [ ] Bug fix
- [ ] Nouvelle fonctionnalité
- [ ] Breaking change
- [ ] Documentation

## Tests
- [ ] Tests unitaires ajoutés/modifiés
- [ ] Tests d'intégration
- [ ] Tests manuels effectués

## Checklist
- [ ] Code respecte les standards
- [ ] Tests passent
- [ ] Documentation mise à jour
- [ ] Changements testés localement
```

### Processus de Review

1. **Assignation** : Assigner des reviewers appropriés
2. **CI/CD** : Tous les checks doivent passer
3. **Review** : Au moins 1 approbation requise
4. **Merge** : Squash and merge recommandé

## 🐛 Rapport de Bugs

### Template d'Issue

```markdown
## Description du Bug
Description claire et concise du bug

## Reproduction
Étapes pour reproduire:
1. Aller à '...'
2. Cliquer sur '...'
3. Voir erreur

## Comportement Attendu
Description du comportement attendu

## Comportement Actuel
Description du comportement actuel

## Environnement
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.12.0]
- Node.js: [e.g., 18.17.0]
- Navigateur: [e.g., Chrome 91]

## Logs
```
Coller les logs d'erreur ici
```

## Captures d'écran
Si applicable, ajouter des captures d'écran
```

## 💡 Demande de Fonctionnalité

### Template Feature Request

```markdown
## Résumé
Brève description de la fonctionnalité

## Problème
Quel problème cette fonctionnalité résout-elle ?

## Solution Proposée
Description de la solution souhaitée

## Alternatives Considérées
Autres solutions envisagées

## Contexte Additionnel
Informations supplémentaires
```

## 📞 Support

### Canaux de Communication

- **Issues GitHub** : Pour bugs et features
- **Discussions** : Pour questions générales
- **Email** : [votre.email@polytech.fr](mailto:votre.email@polytech.fr)

### Temps de Réponse

- **Bugs critiques** : 24h
- **Demandes de fonctionnalités** : 1 semaine
- **Questions** : 2-3 jours

---

Merci pour votre contribution ! 🚀

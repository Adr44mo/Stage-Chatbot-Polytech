# 🤝 Guide de Contribution - New Filler

## 🎯 Avant de Contribuer

Merci de votre intérêt pour améliorer le module `new_filler` ! Ce guide vous aidera à contribuer efficacement.

## 📋 Prérequis

### Environnement de Développement
```bash
# Python 3.12+
python --version

# Dépendances principales
pip install langchain langgraph openai chromadb jsonschema

# Variables d'environnement
echo "OPENAI_API_KEY=your_key" > .env
```

### Compréhension du Projet
1. 📚 Lire le [README principal](README.md)
2. 📊 Consulter le [rapport de qualité](QUALITY_REPORT.md)
3. 🕸️ Comprendre l'[architecture du graphe](graph/README.md)

## 🐛 Signaler des Bugs

### Template d'Issue
```markdown
## 🐛 Bug Report

**Description**: Description claire du problème
**Steps to Reproduce**: Étapes pour reproduire
**Expected Behavior**: Comportement attendu
**Actual Behavior**: Comportement observé
**Environment**: OS, Python version, dépendances

**Logs**:
```
[Coller les logs pertinents]
```

**Files**:
- Fichiers d'exemple causant le problème
```

## ✨ Proposer des Améliorations

### Types de Contributions Bienvenues
1. 🧪 **Tests** - Ajout de tests unitaires/intégration
2. 📚 **Documentation** - Amélioration des docs
3. 🚀 **Performance** - Optimisations
4. 🔧 **Fonctionnalités** - Nouveaux types de documents
5. 🛡️ **Robustesse** - Gestion d'erreurs

### Template de Feature Request
```markdown
## ✨ Feature Request

**Problem Statement**: Quel problème cela résout-il ?
**Proposed Solution**: Solution détaillée
**Alternatives Considered**: Autres approches envisagées
**Impact**: Qui bénéficiera de cette fonctionnalité ?
```

## 🔄 Workflow de Développement

### 1. Setup Local
```bash
# Fork du repo et clone
git clone your-fork-url
cd new_filler

# Créer une branche feature
git checkout -b feature/your-feature-name
```

### 2. Développement

#### Structure de Code
```python
# Toujours documenter les fonctions
def my_new_function(data: dict) -> dict:
    """
    Description claire de la fonction.
    
    Args:
        data: Description du paramètre
        
    Returns:
        dict: Description du retour
        
    Raises:
        ValueError: Quand l'input est invalide
    """
    # Implementation
    return result
```

#### Tests Requis
```python
# tests/test_your_feature.py
import pytest
from new_filler.logic.your_module import your_function

def test_your_function_success():
    """Test du cas nominal"""
    input_data = {"key": "value"}
    result = your_function(input_data)
    assert result["expected_key"] == "expected_value"

def test_your_function_error():
    """Test de gestion d'erreur"""
    with pytest.raises(ValueError):
        your_function(invalid_data)
```

### 3. Standards de Code

#### Style Python
```python
# ✅ Bon
def process_document(file_path: str) -> dict:
    """Process a document and return structured data."""
    
# ❌ Mauvais  
def process(f):
    # pas de doc, types peu clairs
```

#### Gestion d'Erreurs
```python
# ✅ Bon
try:
    result = risky_operation()
    log_callback(state, f"SUCCESS: {operation}")
    return result
except SpecificError as e:
    state["error"] = f"Specific error: {e}"
    log_callback(state, f"ERROR: {e}")
    raise
    
# ❌ Mauvais
try:
    result = risky_operation()
except:
    pass  # Silent fail
```

#### Logging
```python
# ✅ Bon
log_callback(state, f"PROCESSING: {file_type} - {file_path}")

# ❌ Mauvais
print("processing file")  # Pas assez d'info
```

### 4. Ajout de Nouveaux Nœuds

#### 1. Créer le Nœud
```python
# graph/nodes.py
def my_new_node(state):
    """
    Description du traitement effectué.
    
    Args:
        state: FillerState avec les données d'entrée
        
    Returns:
        FillerState: État mis à jour
    """
    try:
        # Votre logique ici
        result = process_data(state["data"])
        state["output_data"] = result
        log_callback(state, "MY_NEW_NODE: SUCCESS")
        return state
    except Exception as e:
        state["error"] = f"My new node error: {e}"
        state["traceback"] = traceback.format_exc()
        log_callback(state, f"MY_NEW_NODE: ERROR - {e}")
        raise
```

#### 2. Intégrer au Graphe
```python
# graph/build_graph.py
def build_graph():
    graph = StateGraph(FillerState)
    
    # Ajouter votre nœud
    graph.add_node("my_new_node", my_new_node)
    
    # Connecter dans le flux
    graph.add_edge("previous_node", "my_new_node")
    graph.add_edge("my_new_node", "next_node")
    
    return graph.compile()
```

### 5. Tests et Validation

#### Tests Unitaires
```bash
# Lancer les tests
pytest tests/ -v

# Coverage
pytest --cov=new_filler tests/
```

#### Tests d'Intégration
```bash
# Test sur fichiers réels
python -m new_filler.main --test-mode
```

#### Validation Manuelle
```bash
# Vérifier le graphe
python -m new_filler.draw_graph

# Analyser les résultats
python analyze_metadata.py
```

## 📝 Pull Request

### Checklist Avant PR
- [ ] ✅ Tests passent
- [ ] 📚 Documentation mise à jour
- [ ] 🧹 Code formaté (black, isort)
- [ ] 🔍 Pas de TODO/FIXME dans le code
- [ ] 📊 Performance acceptable
- [ ] 🛡️ Gestion d'erreurs robuste

### Template de PR
```markdown
## 🎯 Description

Brief description des changements.

## 🔧 Type de Changement
- [ ] 🐛 Bug fix
- [ ] ✨ Nouvelle fonctionnalité
- [ ] 🚀 Performance
- [ ] 📚 Documentation
- [ ] 🧪 Tests

## 🧪 Tests
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Tests d'intégration validés
- [ ] Tests manuels effectués

## 📊 Impact
- **Performance**: Aucun impact / Amélioration / Dégradation acceptable
- **Breaking Changes**: Oui / Non
- **Dependencies**: Nouvelles dépendances : [liste]

## 📋 Checklist
- [ ] Code review auto effectué
- [ ] Documentation mise à jour
- [ ] Tests passent
- [ ] Changements testés manuellement
```

## 🚀 Déploiement

### Version et Release
```bash
# Versioning sémantique
# MAJOR.MINOR.PATCH
# 1.0.0 -> 1.0.1 (bug fix)
# 1.0.0 -> 1.1.0 (nouvelle feature)
# 1.0.0 -> 2.0.0 (breaking change)
```

### Validation Finale
1. 🧪 **Tests complets** sur environnement de test
2. 📊 **Analyse de performance** sur données réelles
3. 🔍 **Review de sécurité** si changements sensibles
4. 📚 **Validation documentation** par utilisateurs finaux

## 🎉 Reconnaissance

Les contributeurs seront ajoutés à :
- 📜 CONTRIBUTORS.md
- 🏆 Section remerciements des releases
- 💬 Mentions dans les communications projet

---

Merci pour votre contribution ! 🙏

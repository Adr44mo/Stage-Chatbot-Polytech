# Utils Module - Utilitaires

## Objectif

Ce module fournit les **utilitaires transversaux** utilisés par l'ensemble du pipeline :
- **Interface IA unifiée** (OpenAI/Ollama)
- **Helpers techniques** réutilisables
- **Abstractions** pour simplifier le code métier

## Structure

```
utils/
└── ollama_wrapper.py    # Interface IA unifiée
```

## ollama_wrapper.py - Interface IA

### Fonctions Principales

#### `ask_model(prompt, engine="openai")`
Interface unifiée pour interroger les modèles IA.

```python
# Utilisation avec OpenAI (par défaut)
response = ask_model("Quel est le type de ce document ?")

# Utilisation avec Ollama
response = ask_model("Classifiez ce contenu", engine="ollama")
```

### Configuration

#### Variables d'Environnement
```env
OPENAI_API_KEY=your_openai_key_here
```

#### Modèles Configurés
```python
OLLAMA_MODEL = "mistral"      # Modèle local Ollama
OPENAI_MODEL = "gpt-4o-mini"  # Modèle OpenAI
```

### Gestion Multi-Moteurs

#### OpenAI (Recommandé)
```python
def ask_openai(prompt: str) -> str:
    """Appel sécurisé à l'API OpenAI"""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3  # Réponses cohérentes
    )
    
    return response.choices[0].message.content.strip()
```

**Avantages** :
- Haute qualité des réponses
- Stabilité du service
- Support multilingue excellent
- Coût par token

#### Ollama (Alternative Locale)
```python
def ask_ollama(prompt: str) -> str:
    """Appel local via subprocess"""
    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt.encode("utf-8"),
        capture_output=True,
        timeout=60
    )
    
    return result.stdout.decode("utf-8").strip()
```

**Avantages** :
- Gratuit et privé
- Pas de limite de tokens
- Fonctionne hors ligne
- Qualité variable selon le modèle
- Plus lent

### Gestion d'Erreurs

#### Erreurs Communes
```python
# Clé API manquante
RuntimeError("Clé API OpenAI manquante")

# Timeout Ollama
RuntimeError("Timeout pendant l'appel à Ollama")

# Erreur réseau OpenAI
RuntimeError("Erreur OpenAI: Rate limit exceeded")
```

#### Stratégie de Fallback
```python
def ask_model_with_fallback(prompt: str) -> str:
    """Essaie OpenAI puis Ollama en fallback"""
    try:
        return ask_model(prompt, engine="openai")
    except Exception as e:
        print(f"OpenAI failed: {e}, trying Ollama...")
        return ask_model(prompt, engine="ollama")
```

### Optimisations Recommandées

#### 1. Cache des Réponses
```python
import functools

@functools.lru_cache(maxsize=128)
def cached_ask_model(prompt_hash: str, prompt: str) -> str:
    """Cache LRU pour éviter les appels redondants"""
    return ask_model(prompt)

# Usage
prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
response = cached_ask_model(prompt_hash, prompt)
```

#### 2. Batch Processing
```python
def ask_model_batch(prompts: List[str]) -> List[str]:
    """Traitement par batch pour optimiser les appels"""
    # Implementation du batching
    pass
```

#### 3. Retry Logic
```python
import tenacity

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    stop=tenacity.stop_after_attempt(3)
)
def ask_model_with_retry(prompt: str) -> str:
    """Retry automatique en cas d'erreur réseau"""
    return ask_model(prompt)
```

## Extensions Possibles

### Nouveaux Utilitaires

#### File Utils
```python
# utils/file_utils.py
def safe_read_file(path: str) -> str:
    """Lecture sécurisée avec gestion d'encodage"""
    
def compute_file_hash(path: str) -> str:
    """Hash SHA256 pour déduplication"""
    
def backup_file(path: str) -> str:
    """Sauvegarde avec timestamp"""
```

#### Text Utils
```python
# utils/text_utils.py
def clean_text(text: str) -> str:
    """Nettoyage standardisé du texte"""
    
def extract_keywords(text: str) -> List[str]:
    """Extraction de mots-clés automatique"""
    
def detect_language(text: str) -> str:
    """Détection de langue"""
```

#### Validation Utils
```python
# utils/validation_utils.py
def validate_json_schema(data: dict, schema: dict) -> bool:
    """Validation JSON Schema améliorée"""
    
def validate_url(url: str) -> bool:
    """Validation d'URL"""
    
def validate_file_type(path: str, allowed_types: List[str]) -> bool:
    """Validation de type de fichier"""
```

## Utilisation

### Import Standard
```python
from utils.ollama_wrapper import ask_model

# Usage simple
response = ask_model("Analysez ce document...")
```

### Configuration Avancée
```python
from utils.ollama_wrapper import ask_openai, ask_ollama

# Contrôle explicite du moteur
if use_openai:
    response = ask_openai(prompt)
else:
    response = ask_ollama(prompt)
```

### Integration avec la Logique Métier
```python
# logic/fill_logic.py
from utils.ollama_wrapper import ask_model

def fill_missing_fields(data: dict, fields: list, prompt_file: str):
    prompt = load_prompt(prompt_file).format(data=data)
    response = ask_model(prompt)  # Interface unifiée
    return parse_response(response)
```

## Monitoring et Métriques

### Métriques Recommandées
```python
import time
from collections import defaultdict

class AIMetrics:
    def __init__(self):
        self.call_count = defaultdict(int)
        self.response_times = defaultdict(list)
        self.error_count = defaultdict(int)
    
    def track_call(self, engine: str, response_time: float, success: bool):
        self.call_count[engine] += 1
        self.response_times[engine].append(response_time)
        if not success:
            self.error_count[engine] += 1
```

### Logs Structurés
```python
import logging

logger = logging.getLogger(__name__)

def ask_model_logged(prompt: str, engine: str = "openai") -> str:
    """Version avec logging détaillé"""
    start_time = time.time()
    
    try:
        response = ask_model(prompt, engine)
        duration = time.time() - start_time
        
        logger.info(f"AI_CALL_SUCCESS", extra={
            "engine": engine,
            "duration_ms": duration * 1000,
            "prompt_length": len(prompt),
            "response_length": len(response)
        })
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error(f"AI_CALL_ERROR", extra={
            "engine": engine,
            "duration_ms": duration * 1000,
            "error": str(e)
        })
        
        raise
```

## Bonnes Pratiques

1. **Sécurité** : Ne jamais logger les clés API
2. **Performance** : Utiliser le cache pour les prompts répétitifs
3. **Robustesse** : Toujours avoir un fallback en cas d'erreur
4. **Monitoring** : Tracker les métriques d'usage et performance
5. **Coût** : Optimiser les prompts pour réduire les tokens

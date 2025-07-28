# Module Logic - Logique Métier

## Objectif

Ce module contient toute la logique métier du pipeline de traitement :
- Classification automatique de documents
- Enrichissement de métadonnées via IA
- Extraction et normalisation de données
- Validation par schéma

## Structure

```
logic/
├── fill_logic.py      # Enrichissement automatique
├── detect_type.py     # Classification de documents
├── webjson.py         # Normalisation JSON web
├── load_pdf.py        # Extraction de contenu PDF
├── syllabus.py        # Traitement spécialisé syllabus
└── chunck_syll.py     # Découpage intelligent pour RAG
```

## fill_logic.py - Enrichissement Automatique

### Fonctions principales

#### `fill_missing_fields(data, fields, prompt_file)`
Enrichit automatiquement les champs manquants via IA.

```python
# Exemple d'usage
metadata = fill_missing_fields(
    data=document_data,
    fields=["title", "secteur", "auteurs"],
    prompt_file="globals/metadata.txt"
)
```

#### `validate_with_schema(data)`
Valide un document selon le schéma JSON Polytech.

```python
is_valid = validate_with_schema(normalized_document)
if not is_valid:
    # Document rejeté
```

#### `extract_json(response)`
Extrait et nettoie le JSON des réponses IA.

```python
# Gère les formats :
# ```json { "key": "value" } ```
# { "key": "value" }
clean_data = extract_json(ai_response)
```

### Pipeline d'Enrichissement
```mermaid
graph LR
    A[Document Brut] --> B[Détecter Type]
    B --> C[Enrichir Métadonnées]
    C --> D[Enrichir Tags]
    D --> E[Enrichir Type Spécifique]
    E --> F[Valider]
    F --> G[Document Enrichi]
```

## detect_type.py - Classification

### Classification automatique
Identifie automatiquement le type de document parmi :
- **cours** : Matériel pédagogique
- **projet** : Documents de projet
- **administratif** : Procédures, règlements
- **specialite** : Information sur spécialités
- **vie_etudiante** : Activités étudiantes
- **infrastructure** : Informations pratiques

```python
doc_type = detect_document_type(content)
# Retourne : "cours", "projet", "administratif", etc.
```

### Algorithme
1. **Analyse du contenu** (premiers 2000 caractères)
2. **Prompt IA spécialisé** pour classification
3. **Validation** du type retourné
4. **Fallback** en cas d'erreur

## webjson.py - Normalisation Web

### Normalisation d'entrées web
Convertit les données scrapées en format Polytech uniforme.

```python
normalized = normalize_entry(
    raw_data=scraped_json,
    chemin_local="/path/to/source",
    site_name="polytech_sorbonne"
)
```

### Transformations Appliquées
- **Nettoyage du contenu** (HTML, caractères spéciaux)
- **Extraction de métadonnées** (titre, date, auteurs)
- **Normalisation des URLs**
- **Classification automatique**

## 📄 load_pdf.py - Extraction PDF

### Types de PDFs Supportés

#### PDFs Manuels
```python
result = process_manual_pdf_file(pdf_path)
# Extraction complète + métadonnées basiques
```

#### PDFs Scrapés
```python
result = process_scraped_pdf_file(pdf_path)
# Extraction + métadonnées enrichies du scraping
```

### Extraction de Données
- **Texte complet** via PyMuPDF/pdfplumber
- **Métadonnées PDF** (auteur, titre, date)
- **Nettoyage automatique** (mise en forme, caractères)

## 🎓 syllabus.py - Traitement Syllabus

### Extraction Structurée
Traite spécifiquement les documents syllabus pour extraire :
- **Structure hiérarchique** des cours
- **Informations pédagogiques** (crédits, prérequis)
- **Planning détaillé**
- **Compétences visées**

```python
syllabus_data = extract_syllabus_structure(pdf_path)
# Structure complète du syllabus
```

## ✂️ chunck_syll.py - Découpage RAG

### Chunking Intelligent
Découpe les syllabus de manière optimale pour la recherche RAG :

```python
chunks = chunk_syllabus_for_rag(syllabus_data)
# Liste de chunks optimisés
```

### Stratégies de Découpage
1. **Respect de la structure** (cours, sections)
2. **Taille optimale** pour embeddings
3. **Préservation du contexte** 
4. **Métadonnées enrichies** par chunk

## Utilisation

### Pipeline complet
```python
from logic.fill_logic import route_document
from logic.detect_type import detect_document_type

# 1. Classification
doc_type = detect_document_type(content)

# 2. Enrichissement complet
enriched_doc = route_document(raw_data)

# 3. Validation
is_valid = validate_with_schema(enriched_doc)
```

### Enrichissement ciblé
```python
from logic.fill_logic import fill_missing_fields

# Enrichir seulement certains champs
tags = fill_missing_fields(
    data=document,
    fields=["tags"],
    prompt_file="globals/tags.txt"
)
```

## Bonnes pratiques

1. **Performance** : Cache les réponses IA pour éviter les appels redondants
2. **Robustesse** : Toujours valider les réponses IA avant usage
3. **Monitoring** : Logger les temps de réponse et taux de succès
4. **Extensibilité** : Utiliser des prompts externalisés pour faciliter les ajustements

---
*Module de logique métier intégré au pipeline New Filler (juillet 2025).*

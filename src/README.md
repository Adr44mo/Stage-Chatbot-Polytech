# README du sous-dossier /src/
Le présent dossier contient les fichiers python (scripts ou imports) secondaires.

- **keys_file.py** est importé dans le main pour obtenir les URL, clés API, tokens par virtual environment
- **llm.py** est importé dans le main et contient des définitions de fonctions de query
- **openai_chroma_search.py** est importé dans le main et contient des définitions de fonctions de retrieval par metadonnées avec une gestion des bdd chromadb
- **prompts.py** est importé dans llm.py et définit le système de prompt engineering
- **vectorisation_generation.py** n'est importé nulle part et doit etre éxécuté seul pour générer/mettre à jour le(s) FAISS/CHROMADB à partir du corpus

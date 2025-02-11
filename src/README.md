# README du sous-dossier /src/
Le present dossier contient les fichiers python (scripts ou imports) secondaires.

- keys_file.py est importé dans le main et contient les URL, clés API, tokens…
- llm.py est importé dans le main et contient des définitions de fonctions de query
- prompts.py est importé dans llm.py et définit le système de prompt engineering
- utils.py n'est importé nulle part et doit etre éxécuté seul pour MàJ les FAISS

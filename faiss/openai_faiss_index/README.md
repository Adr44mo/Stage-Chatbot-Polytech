# README du sous-dossier /openai_faiss_index/

Le present dossier contient l'index FAISS créé à partir du corpus avec les embeddings de chez **OpenAI**. Le tout sert au RAG lorsqu'il utilise **GPT**.
Si vous souhaitez mettre les données du retriever à jour, veuillez supprimer/modifier/ajouter les PDF voulus dans le dossier **/corpus/**, soit en scrappant soit en les ajoutant manuellement.
Puis exécutez le script **/src/faiss_generation.py** et choisissez **modèle OpenAI (1)**. Le fichier **log.txt** indique la date de dernière génération de l'index faiss, et la liste des fichiers PDF utilisés pour le générer.
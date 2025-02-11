# README du sous-dossier /llama_faiss_index/

Le present dossier contient l'index FAISS créé à partir du corpus avec les embeddings Ollama. Le tout sert au RAG lorsqu'il s'addresse à llama.
Si vous souhaitez mettre les données du retriever à jour, veuillez supprimer/modifier/ajouter les PDF voulus dans le dossier _/corpusv1.4/pdf/_ .
Puis, définissez le modèle par défaut dans le config.yaml à _llama3_. Enfin, exécutez le script _/src/utils.py_ .
# README du sous-dossier /openai_faiss_index/

Le present dossier contient l'index FAISS créé à partir du corpus avec les embeddings de chez OpenAI. Le tout sert au RAG lorsqu'il s'addresse à GPT.
Si vous souhaitez mettre les données du retriever à jour, veuillez supprimer/modifier/ajouter les PDF voulus dans le dossier _/corpusv1.4/pdf/_ .
Puis, définissez le modèle par défaut dans le config.yaml à _gpt-4o_. Enfin, exécutez le script _/src/utils.py_ .
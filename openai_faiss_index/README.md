# README du sous-dossier /openai_faiss_index/

Le present dossier contient l'index FAISS créé à partir du corpus avec les embeddings de chez **OpenAI**. Le tout sert au RAG lorsqu'il s'addresse à **GPT**.
Si vous souhaitez mettre les données du retriever à jour, veuillez supprimer/modifier/ajouter les PDF voulus dans le dossier **/corpusv1.4/pdf/** .
Puis, définissez le modèle par défaut **default_model_faiss** dans le **config.yam** à **gpt-4o**. Enfin, exécutez le script **/src/utils.py** .
# README du sous-dossier /llama_faiss_index/

Le present dossier contient l'index FAISS créé à partir du corpus avec les embeddings de chez **nomic-embed-text-v1-5-vxq** de Hugging Face. Le tout sert au RAG lorsqu'il s'addresse à **llama**.
Si vous souhaitez mettre les données du retriever à jour, veuillez supprimer/modifier/ajouter les PDF voulus dans le dossier **/corpus/**, soit en scrappant soit en les ajoutant manuellement.
Puis, définissez le modèle par défaut **default_model_faiss** dans le **config.yaml** à **llama3**. Enfin, exécutez le script **/src/faiss_generation.py**. \ \ Le fichier **log.txt** indique la 
date de génération de l'index faiss, et liste les fichiers PDF ayant été utilisés pour le générer.
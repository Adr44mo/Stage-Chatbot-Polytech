# Projet PolyChat

Dernière mise à jour : 11 février 2025 \
Développement toujours en cours

## Introduction

Ce repo contient les fichiers constitutifs d'un framework _RAG (Retrieval-Augmented Generation)_. Ce RAG est destiné à être utilisé comme ChatBot de l'école d'ingénieurs Polytech-Sorbonne. Il est encore en cours de développement.

## Fonctionnement

Le _Corpus_ est l'ensemble des documents dans lequel le _RAG_ peut puiser ses informations. Il doit donc être constitué de documents pertinents et variés en quantité suffisante. Dans cette version du projet, seuls les PDF sont pris en compte. Une version hybride PDF/JSON avec web-scraping est encore en cours de développement.   
Ces documents sont ensuite transformés en _embeddings_ (des représentations mathématiques vectorielles) selon la méthode d'_OpenAI (OpenAIEmbeddings)_. Une fois ces embeddings créés, ils sont stockés dans un index vectoriel local _FAISS (Facebook AI Similarity Search)_.   
L'index est ensuite utilisé pour créer un _retriever_, un outil permettant de rechercher efficacement les documents les plus pertinents en fonction d'une requête. Ce retriever est alors intégré au modèle _ChatOpenAI_ auquel il fournit (à chaque requête) des informations pertinentes issues du corpus.   
Le _LLM (Large Language Model)_ utilisé est _gpt-4o-mini_ car il présente un bon compromis efficacité/rapidité. Des essais sont encore en cours avec d'autres versions de _GPT_ et de _LLAMA_. Des évaluations par _BERT-Score_ sont également en cours.  
Enfin, le tout est mis sous forme de ChatBot avec une interface _Streamlit_ customisée. L'hébergement est fait sur un VPS, et l'interface est streamée sous forme d'iframe sur [ce site web maquette](https://www.maquettepolytechrag.ovh/). 
Une version locale alternative utilisant des filtres de métadonnée est encore à l'essai et est disponible dans le dossier _test-RAG-metadata_ .

## Comment accéder aux VPS de déploiement web 

- Le VPS distant faisant tourner le code python est accessible sur [ce site web d'hébergement](https://www.render.com/). Il utilise peu de ressources et d'argent.
- Le VPS distant faisant tourner llama3-8b est accessible sur [ce site web d'endpoint](https://endpoints.huggingface.co/). Il utilise beaucoup de ressources et 3$/h lorsqu'il n'est pas en veille.
- Pour se connecter à ces VPS, demandez les identifiants à Tristan en privé.

## Résultats

Voici les qualités actuelles du ChatBot :

- Il répond rapidement et de manière concise
- Ses prompts lui évitent de divaguer et de parler de sujets hors-Polytech
- Son historique web est fonctionnel
- Le switch entre les différents LLM proposés (gpt-4o, gpt-4o-mini, llama3) est fonctionnel
- Son interface est visuellement plutôt plaisante et complète
- Son déploiement web est faisable via injection HTML + JavaScript sur tout CMS

Et voici ses défauts :

- Son corpus pourrait être mieux fourni et nécessite encore un entretien manuel
- L'utilisation du LLM LLAMA est encore incompatible avec le retrieving. Cela sera mis à jour dans la prochaine update majeure.
- L'utilisation du LLM LLAMA nécessite de grosses ressources physiques (notamment GPU) et ne tourne donc assez rapidement que sur un VPS ou un serveur local très puissant
- Le déploiement web distant (VPS pour le dossier + VPS pour llama) à partir de 0 prend une dizaine de minutes
- En cas de déploiement web distant, le VPS hébergeant llama doit être mis en veille pour ne pas trop facturer tristan. Il ne sert donc actuellement qu'au test.
- Le système est conçu pour un web-déploiement et nécessite quelques adaptations pour tourner en local

## Auteurs

Samuel (MAIN5)
Tristan (MAIN5)
Amalia (MAIN5)
Yannick (MAIN5)
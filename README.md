# Projet-Chatbot

Dernière mise à jour : 17 janvier 2025
Développement toujours en cours

## Introduction

Ce repo contient les fichiers constitutifs d'un framework _RAG (Retrieval-Augmented Generation)_. Ce RAG est destiné à être utilisé comme ChatBot de l'école d'ingénieurs Polytech-Sorbonne. Il est encore en cours de développement.

## Fonctionnement

Le _Corpus_ est l'ensemble des documents dans lequel le _RAG_ peut puiser ses informations. Il doit donc être constitué de documents pertinents et variés en quantité suffisante. Dans cette version du projet, seuls les PDF sont pris en compte. Une version hybride PDF/JSON avec web-scraping est encore en cours de développement.
Ces documents sont ensuite transformés en _embeddings_ (des représentations mathématiques vectorielles) selon la méthode d'_OpenAI (OpenAIEmbeddings)_. Une fois ces embeddings créés, ils sont stockés dans un index vectoriel local _FAISS (Facebook AI Similarity Search)_.
L'index est ensuite utilisé pour créer un _retriever_, un outil permettant de rechercher efficacement les documents les plus pertinents en fonction d'une requête. Ce retriever est alors intégré au modèle _ChatOpenAI_ auquel il fournit (à chaque requête) des informations pertinentes issues du corpus.
Le _LLM (Large Language Model)_ utilisé est _gpt-4o-mini_ car il présente un bon compromis efficacité/rapidité. Des essais sont encore en cours avec d'autres versions de _GPT_ et de _LLAMA_. Des évaluations par _BERT-Score_ sont également en cours.
Enfin, le tout est mis sous forme de ChatBot avec une interface _Streamlit_ customisée. L'hébergement est fait sur un VPS, et l'interface est streamée sous forme d'iframe sur [ce site web maquette](https://www.maquettepolytechrag.ovh/).

## Résultats

Voici les qualités actuelles du ChatBot :

- Il répond rapidement et de manière concise
- Ses prompts lui évitent de divaguer et de parler de sujets hors-Polytech
- Son historique à base de cookies est fonctionnel
- Son interface est visuellement plutôt plaisante
- Son déploiement web est faisable via injection HTML + JavaScript sur tout CMS

Et voici ses défauts :

- Il peut parfois halluciner
- Il fait quelques confusions entre les filières
- Son corpus n'est pas assez fourni et nécessite encore un entretien manuel
- Il lui manque une solution d'hébergement tout-en-un pérenne

## Auteurs

Samuel (MAIN5)
Tristan (MAIN5)
Amalia (MAIN5)
Yannick (MAIN5)
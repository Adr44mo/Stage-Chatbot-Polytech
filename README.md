# Projet PolyChat

Dernière mise à jour : 20 février 2025 \
Développement terminé
Soutenance effectuée

## Introduction

Ce repo contient les fichiers constitutifs d'un framework _RAG (Retrieval-Augmented Generation)_. Ce RAG est destiné à être utilisé comme ChatBot de l'école d'ingénieurs Polytech-Sorbonne.

## Fonctionnement

Le _Corpus_ est l'ensemble des documents dans lequel le _RAG_ peut puiser ses informations. Il doit donc être constitué de documents (PDF et JSON) pertinents et variés en quantité suffisante.
Ces documents sont ensuite transformés en _embeddings_ (des représentations mathématiques vectorielles) selon diverses méthodes. Une fois ces embeddings créés, ils sont stockés dans un index vectoriel local.   
L'index est ensuite utilisé pour créer un _retriever_, un outil permettant de rechercher efficacement les documents les plus pertinents en fonction d'une requête. Ce retriever est alors intégré au modèle de LLM auquel il fournit (à chaque requête) des informations pertinentes issues du corpus.   
Les _LLM (Large Language Model)_ utilisés sont _gpt-4o_ et _gpt-4o-mini_ car ils présentent un bon compromis efficacité/rapidité. _LLaMA3-8B_ est également disponible car il explore la possibilité d'un LLM tournant en local.
Enfin, le tout est mis sous forme de ChatBot avec une interface _Streamlit_ customisée. L'hébergement est fait sur un VPS, et l'interface est streamée sous forme d'iframe sur [ce site web maquette](https://www.maquettepolytechrag.ovh/). Vous pouvez y sélectionner vous-même le LLM avec lequel vous souhaitez parler.

## Comment accéder aux VPS de déploiement web [OUTDATED]

La logique suivante était utilisée jusqu'en février 2025, date de fin du projet de développement. Les nouveaux VPS utilisés par les personnes ayant repris le projet sont probablement différents :

- Le VPS distant faisant tourner le code python est accessible sur [ce site web d'hébergement](https://www.render.com/). Il utilise peu de ressources et d'argent.
- Les VPS distant faisant tourner llama3-8b et son serveur d'embeddings sont accessibles sur [ce site web d'endpoint](https://endpoints.huggingface.co/). Il utilise beaucoup de ressources et 3$/h lorsqu'il n'est pas en veille.
- Les identifiants sont privés et réservés à l'équipe de maintenance PolyTech.

## Résultats

Voici les qualités du ChatBot en février 2025 :

- Il répond rapidement et de manière concise
- Ses prompts lui évitent de divaguer et de parler de sujets hors-Polytech
- Son historique web est fonctionnel
- Le switch entre les différents LLM proposés (gpt-4o, gpt-4o-mini, llama3) marche en un clic
- 3 logiques sont proposées : retrieval sur FAISS avec gpt-4o-mini ou LLaMA, et retrieval (avec metadata) sur ChromaDB avec gpt-4o
- Son interface est visuellement plutôt plaisante et complète
- Son déploiement web est faisable via injection HTML + JavaScript sur tout CMS
- Sa configuration à base de YAML le rend flexible et facile à adapter
- Son web-scraping est automatique, fonctionnel et clair

Et voici ses défauts en février 2025 :

- L'utilisation du LLM LLAMA nécessite de grosses ressources physiques (notamment GPU) et ne tourne donc assez rapidement que sur un VPS ou un serveur local puissant
- Le déploiement web distant (VPS pour le dossier + VPS pour llama) à partir de 0 prend une dizaine de minutes
- En cas de déploiement web distant, le VPS hébergeant llama doit être mis en veille pour ne pas trop facturer tristan. Il ne sert donc actuellement qu'au test et sera amené à changer.
- Le système est conçu pour un web-déploiement et nécessite quelques adaptations pour tourner en local (essentiellement au niveau de la logique d'historique par URL)
- Le front-end ne gère pas bien le responsive (affichage sur téléphone portable etc)

## Auteurs (étudiants de la MAIN5 2024-2025)

Samuel,
Tristan,
Amalia,
Yannick

## Encadrant (responsable de la MAIN5 2024-2025)

M. TANNIER
# Test commit

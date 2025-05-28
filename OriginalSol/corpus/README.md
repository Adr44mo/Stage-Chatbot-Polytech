# README du sous-dossier /corpus/
Le présent dossier contient le corpus, qui englobe l'ensemble des documents (PDF ou JSON) dans lesquels le modèle de RAG pioche (au travers d'une vectorisation par FAISS ou chromadb) pour fournir des réponses personnalisées.

- **/json_scrapes/** contient les fichiers JSON récoltés (=scrapés) automatiquement par l'outil de scraping.
- **/pdf_ajoutes_manuellement** contient les fichiers PDF qui ne peuvent pas être récoltés par l'outil de scraping parce qu'ils ne sont pas présents sur le site. Ce dossier ne peut donc être alimenté que manuellement, en glissant-déposant les PDF que vous souhaitez ajouter.
- **/pdf_scrapes** contient les fichiers PDF récoltés (=scrapés) automatiquement par l'outil de scraping.
- **/scraping_tool/** contient l'outil python permettant de réaliser le scraping très simplement. Il doit être lancé manuellement.

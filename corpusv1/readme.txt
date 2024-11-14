Répertoires :
- 'intranet' correspond aux documents internes publics auprès des élèves (règlement des études, maquettes pédagogiques à jour, etc)
- 'polytech.sorbonne-universite.fr' correspond au site web de Polytech sorbonne. l'agencement du répertoire suit la structure web du site pour que l'on s'y retrouve mieux.
- 'les_json_parfaits_en_vrac' correspond à l'ensemble des json regroupés dans un seul et même dossier si l'on veut se passer de l'arborescence. Ils ont été fait manuellement de la manière la plus claire et préférable. On souhaiterait donc que le script de scrapt puisse régénérer la même chose automatiquement, ce qui ne sera bien sûr pas possible à 100% pour les raisons évoquées dans le fichier "problemes_scrap.txt"

Structure :
- La structure des répertoires essaie de s'approcher le plus possible de l'agencement réel du site, mais a parfois dû être modifiée pour éviter les redondances ou pour s'adapter aux différentes structures des pages. Toute l'information textuelle pertinente a néanmoins été conservée.

Fichiers :
- 'readme.txt' est le présent fichier explicatif
- 'problemes_scrap.txt' explique les problèmes à surmonter pour réaliser un script de scrapping efficace
- 'script_scrap.py': Le script principal pour l'extraction de contenu.
- 'requirements.txt': Contient les dépendances Python nécessaires, installables via pip install -r requirements.txt.
- 'scrape.log': Le fichier de log généré lors de chaque exécution du script, contenant les informations sur les pages scrappées et les erre

Courte explication de la manière dont on a stocké les données :

On a opté pour un format .json (JavaScript Object Notation).
L'avantage par rapport au .txt est la possibilité d'agencer le texte et d'attribuer des metadonnées.
L'avantage par rapport au .csv est la capacité à traiter correctement des textes relativement longs.
L'avantage par rapport au .pdf est une bien meilleure structuration (les pdf sont structurés graphiquement plutot que logiquement)
L'avantage par rapport au .jsonl est de pouvoir mieux charger les documents avec langchain (via le JSON Loader).

Choix des metadata :

Certaines metadonnées se révèlent peu utiles dans notre contextes :
- L'auteur d'une publication import peu puisque l'ensemble vient de toute manière de polytech
- La date de publication et d'édition n'importe pas beaucoup plus, mais peut parfois être utile :

Les metadata les plus importantes sont en réalité celles de structuration :
- datespecifique correspond à une temporalité auquel le document fait référence (et non pas est publié) et prend "NA" sinon.
   par exemple, "datespecifique" d'un article concernant un tournoi de 2023 prendrait la valeur "2023" puisqu'il concerne surtout cette année.
- category1 correspond à la source de la page (site Polytech global, site Polytech sorbonne, intranet, site s-u...)
- category2 correspond à la première grande catégorie sur le site même
- category3 correspond à la première sous-catégorie sur le site
- category4 correspond à la deuxième sous-catégorie sur le site
Parfois, l'imbrication n'est pas si profonde, et dans ce cas les category non-atteintes prennent la valeur "NA".
- filierespecifique (exemple : "MAIN") indique si le document concerne une/des filière(s) en particulier, et prend "NA" sinon.

Fonctionnement du Script:

- Le script 'script_scrap.py' extrait automatiquement le contenu textuel principal à l'aide de la librairie readability pour obtenir une version épurée des pages.
Un fichier 'scrape.log' est généré à chaque exécution, consignant les URL traitées, les éventuelles erreurs, et le statut de chaque extraction. Ce log est également affiché dans le terminal.
Gestion des PDFs:
- Les liens vers les fichiers PDF identifiés sur le site sont détectés mais non traités actuellement (commenté comme # TODO: Handle PDFs).
Exécution:
- Pour utiliser le script, exécutez `python script_scrap.py`. Le répertoire scraped_data est créé pour stocker les données JSON extraites.
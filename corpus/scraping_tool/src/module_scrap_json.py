import os
import re
import json
import time
import unicodedata
import urllib.parse
from collections import deque

import requests
from bs4 import BeautifulSoup
import yaml

# Charger la configuration depuis config.yaml
config_path = os.path.join(os.path.dirname(__file__), "../config_scrap.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Récupération des paramètres depuis le YAML
BASE_URL = config.get("BASE_URL")
JSON_DOWNLOAD_DIR = config.get("JSON_DOWNLOAD_DIR")
DICO_URL_SPECIALITES = config.get("DICO_URL_SPECIALITES", {})
JSON_EXCLUDE_STRINGS = config.get("JSON_EXCLUDE_STRINGS", [])

# Définition du domaine pour filtrer les URLs internes
DOMAIN = urllib.parse.urlparse(BASE_URL).netloc.replace("www.", "")

# Création du dossier de sauvegarde si nécessaire
if not os.path.exists(JSON_DOWNLOAD_DIR):
    os.makedirs(JSON_DOWNLOAD_DIR)

# Ensemble des URLs déjà visitées
visited_urls = set()

# Compteur des nouveaux JSON réellement enregistrés
new_json_count = 0

# Texte du footer à exclure s'il apparaît dans le contenu
FOOTER_TEXT = (
    "sciences-polytech-secretariat-agral@sorbonne-universite.fr\n"
    "Bât. Esclangon, 4 place Jussieu\n"
    "Case courrier 135,\n"
    "75252 Paris Cedex 05\n"
    "Tél +33 (0) 1 44 27 73 13\n"
    "Réalisé par l'\n"
    "Agence UX Paris\n"
    "- Feel & Clic"
)

def normalize_title(title):
    """
    Normalise le titre pour en faire un nom de fichier.
    - Transforme les majuscules en minuscules.
    - Remplace les caractères accentués par leurs équivalents non accentués.
    - Remplace la ligature "œ" par "oe".
    - Remplace les espaces et caractères non alphanumériques par des underscores.
    Exemple : "Le cœur de l'histoire" -> "le_coeur_de_l_histoire.json"
    """
    # Remplacer la ligature œ par oe (et sa majuscule)
    title = title.replace("œ", "oe").replace("Œ", "OE")
    
    # Normaliser les accents
    nfkd_form = unicodedata.normalize('NFKD', title)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    
    only_ascii = only_ascii.lower().strip()
    title_norm = re.sub(r'\W+', '_', only_ascii)
    title_norm = title_norm.strip('_')
    return title_norm + ".json"

def extract_category(url):
    """
    Extrait la catégorie à partir du chemin de l'URL.
    On considère que la catégorie est le deuxième élément non vide du path,
    ou le premier si un seul élément est présent.
    """
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split('/') if part]
    if len(parts) >= 2:
        return parts[1]
    elif parts:
        return parts[0]
    else:
        return "NA"

def get_filierespecifique(url):
    """
    Parcours le dictionnaire des spécialités et retourne la clé correspondant à l'URL si trouvée,
    sinon retourne "NA".
    """
    for key, url_list in DICO_URL_SPECIALITES.items():
        if url in url_list:
            return key
    return "NA"

def clean_content(soup):
    """
    Nettoie le contenu pour n'inclure que le texte :
    - Supprime les balises script et style.
    - Remplace les balises <a> par leur texte uniquement.
    - Supprime les images, vidéos et autres éléments non textuels.
    """
    for script in soup(["script", "style"]):
        script.decompose()

    for a in soup.find_all("a"):
        a.replace_with(a.get_text())

    for tag in soup.find_all(["img", "video", "iframe", "object", "embed"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    content = "\n".join([line for line in lines if line])
    # Supprimer le footer s'il apparaît dans le contenu
    if FOOTER_TEXT in content:
        content = content.replace(FOOTER_TEXT, "").strip()
    return content

def extract_title(soup, url):
    """
    Extrait le titre de la page en privilégiant :
    - le contenu de la balise <h1>,
    - puis la balise <title>,
    - sinon une partie de l'URL.
    """
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split('/') if part]
    return parts[-1] if parts else "no_title"

def is_valid_url(url):
    """
    Vérifie que l'URL est bien interne (du domaine de l'école) et qu'elle commence par http ou https.
    Exclut également les URLs dont le chemin contient l'une des chaînes spécifiques définies dans JSON_EXCLUDE_STRINGS.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return False
    if DOMAIN not in parsed.netloc:
        return False
    # Appliquer les exclusions uniquement sur le chemin
    path = parsed.path
    for excl in JSON_EXCLUDE_STRINGS:
        if excl in path:
            return False
    return True

def scrape_page(url):
    global new_json_count
    try:
        response = requests.get(url, timeout=10)
    except Exception as e:
        print(f"[ERROR] Erreur lors de la requete sur {url} : {e}")
        return []

    if response.status_code != 200:
        print(f"Statut {response.status_code} pour {url}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    title = extract_title(soup, url)
    article = soup.find("article")
    if article:
        content = clean_content(article)
    else:
        paragraphs = soup.find_all("p")
        content = "\n".join([clean_content(p) for p in paragraphs if p.get_text(strip=True)])

    if not content.strip():
        print(f"[WARNING] Contenu vide pour : {url}")
        return []

    parsed = urllib.parse.urlparse(url)
    site = parsed.netloc.replace("www.", "")
    category = extract_category(url)
    filiere = get_filierespecifique(url)

    json_obj = {
        "url": url,
        "site": site,
        "category": category,
        "title": title,
        "filierespecifique": filiere,
        "datespecifique": "NA",
        "content": content,
    }

    filename = normalize_title(title)
    filepath = os.path.join(JSON_DOWNLOAD_DIR, filename)

    # Vérification de l'existence et de l'identité du fichier
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            if existing_data == json_obj:
                print(f"[INFO] Fichier identique déjà présent : {filepath}")
                # On ne considère pas ce fichier comme nouveau
                # et on passe à la suite sans réécriture.
                return extract_new_urls(soup, url)
            else:
                print(f"[INFO] Fichier existant différent pour {filepath}. Mise à jour en cours.")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la lecture du fichier existant {filepath} : {e}")
    
    # Enregistrement (création ou mise à jour) du fichier JSON
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=4)
        print(f"[DOWNLOAD] Téléchargement de : {filepath}")
        new_json_count += 1
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'écriture du fichier {filepath} : {e}")

    return extract_new_urls(soup, url)

def extract_new_urls(soup, url):
    """
    Extrait les nouvelles URLs internes depuis la page pour alimenter le crawl.
    """
    new_urls = []
    for a in soup.find_all("a", href=True):
        try:
            href = a['href']
            abs_url = urllib.parse.urljoin(url, href)
            abs_url = abs_url.split("#")[0].rstrip("/")
            if is_valid_url(abs_url) and abs_url not in visited_urls:
                new_urls.append(abs_url)
        except Exception as e:
            print(f"[ERROR] Erreur lors du traitement d'URL : {e}")
            continue
    return new_urls

def crawl(start_url):
    """
    Crawl récursivement les pages internes du site à partir de start_url.
    Le crawl s'arrête lorsque toutes les pages accessibles ont été visitées.
    """
    queue = deque([start_url])
    while queue:
        current_url = queue.popleft()
        if current_url in visited_urls:
            continue
        print(f"[SCRAPING] Page : {current_url}")
        visited_urls.add(current_url)
        new_urls = scrape_page(current_url)
        for url in new_urls:
            if url not in visited_urls:
                queue.append(url)
        time.sleep(1)  # Pause pour éviter de surcharger le serveur

if __name__ == "__main__":
    crawl(BASE_URL)
    print("\n[SCRAP TERMINÉ]")
    print(f"Pages visitées: {len(visited_urls)}")
    print(f"Nouveaux JSON enregistrés : {new_json_count}")

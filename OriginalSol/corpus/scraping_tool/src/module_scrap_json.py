# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
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

# ------------------------------------------------------------------
# Chargement et récupération des paramètres de scrap depuis le .YAML
# ------------------------------------------------------------------

# Chargement
config_path = os.path.join(os.path.dirname(__file__), "../config_scrap.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Récupération
BASE_URL = config.get("BASE_URL")
JSON_DOWNLOAD_DIR = config.get("JSON_DOWNLOAD_DIR")
DICO_URL_SPECIALITES = config.get("DICO_URL_SPECIALITES", {})
JSON_EXCLUDE_STRINGS = config.get("JSON_EXCLUDE_STRINGS", [])
EXACT_URLS_TO_EXCLUDE = config.get("JSON_EXACT_URLS_TO_EXCLUDE", [])
FOOTER_TEXT = config.get("WEBSITE_FOOTER_TEXT", "").strip()


# ---------------------------
# Initialisation de variables
# ---------------------------

DOMAIN = urllib.parse.urlparse(BASE_URL).netloc.replace("www.", "")
if not os.path.exists(JSON_DOWNLOAD_DIR):
    os.makedirs(JSON_DOWNLOAD_DIR)
visited_urls = set()
new_json_count = 0

# -----------------------------------------------------------------
# Fonction pour normaliser un titre pour en faire un nom de fichier
# -----------------------------------------------------------------

def normalize_title(title):

    # Remplacer l'e dans l'o par oe (et sa majuscule)
    title = title.replace("œ", "oe").replace("Œ", "OE")
    
    # Normaliser les accents
    nfkd_form = unicodedata.normalize('NFKD', title)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    
    # Casse et accents
    only_ascii = only_ascii.lower().strip()
    title_norm = re.sub(r'\W+', '_', only_ascii)
    title_norm = title_norm.strip('_')
    return title_norm + ".json"

# ----------------------------------------------------------------
# Fonction pour extraire la 'category" a partir du chemin de l'URL
# ----------------------------------------------------------------

def extract_category(url):

    #Extrait la catégorie à partir du chemin de l'URL.
    #On considère que la catégorie est le deuxième élément non vide du path,
    #ou alorsle premier si un seul élément est présent.
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split('/') if part]
    if len(parts) >= 2:
        return parts[1]
    elif parts:
        return parts[0]
    else:
        return "NA"
    
# ---------------------------------------------------------------------
# Fonction pour déterminer si l'url correspond à une 'filierspecifique'
# ---------------------------------------------------------------------

def get_filierespecifique(url):
    
    # Si l'url est une valeur de 'DICO_URL_SPECIALITES', on retourne sa clé
    for key, url_list in DICO_URL_SPECIALITES.items():
        if url in url_list:
            return key
        
    # Sinon, on initialise 'filierespecifique' à 'NA'
    return "NA"

# -------------------------------------------------------------
# Fonction pour nettoyer le content et n'y inclure que le texte
# -------------------------------------------------------------

def clean_content(soup):

    # On supprime les balises de script et de style
    for script in soup(["script", "style"]):
        script.decompose()

    # Pour les balises <a>, on remplace par le texte
    for a in soup.find_all("a"):
        a.replace_with(a.get_text())

    # On supprime les balises d'images, de vidéos, etc.
    for tag in soup.find_all(["img", "video", "iframe", "object", "embed"]):
        tag.decompose()

    # On extrait le texte après suppression des éléments indésirables
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    content = "\n".join([line for line in lines if line])

    return content

# ------------------------------------------------
# Fonction pour déterminer le titre d'une page web
# ------------------------------------------------

def extract_title(soup, url):
    
    # On essaie de trouver h1
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    
    #     les h2 ne sont pas toujours un bon match
    #     décommenter le code suivant si vous voulez essayer sur les h2 :
    # h2 = soup.find("h2")
    # if h2 and h2.get_text(strip=True):
    #     return h2.get_text(strip=True)
    
    # Sinon on essaie de trouver title
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    
    # Sinon une partie de l'URL
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split('/') if part]
    return parts[-1] if parts else "no_title"

# ----------------------------------------------
# Fonction pour déterminer si une URL est valide
# ----------------------------------------------

def is_valid_url(url):
    
    # On évite les URLs problématiques
    canonical_url = url.rstrip('/')
    if canonical_url in EXACT_URLS_TO_EXCLUDE:
        return False

    # On parse
    parsed = urllib.parse.urlparse(url)

    # On évite les URL sans http/https
    if parsed.scheme not in ["http", "https"]:
        return False
    
    # On évite les URL hors du site de l'école
    if DOMAIN not in parsed.netloc:
        return False
    
    # On applique les exclusions sur la partie découpée de l'URL
    path = parsed.path
    for excl in JSON_EXCLUDE_STRINGS:
        if excl in path:
            return False
    return True

# ------------------------------------------
# Fonction gérant le scraping d'une page web
# Cette fonction n'est PAS récursive, celle
# du module de scrap PDF l'est en revanche.
# ------------------------------------------

def scrape_page(url):

    # Variable globale pour garder le compte des téléchargements effectués
    global new_json_count

    # Requete pour accéder à la page
    try:
        response = requests.get(url, timeout=10)
    except Exception as e:
        print(f"[ERROR] Erreur lors de la requete sur {url} : {e}")
        return []
    if response.status_code != 200:
        print(f"Statut {response.status_code} pour {url}")
        return []

    # On parse la page avec BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # On extrait le titre et on trouve les articles
    title = extract_title(soup, url)
    article = soup.find("article")

    # Traitement s'il y a un article
    if article:
        content = clean_content(article)

    # Traitement s'il n'y a pas d'article (ex : les pages des spécialités)
    else:
        # On sélectionne les divs pertinents
        bloc_divs = soup.find_all("div", class_="bloc-formation")
        bloc_divs_with_h2 = [d for d in bloc_divs if d.find("h2")]

        # On y fait les sélections et le traitement voulu
        if bloc_divs_with_h2:
            content_parts = []
            for div in bloc_divs_with_h2:
                elements = div.find_all(["p", "ul", "span", "h2", "h3"])
                for elem in elements:
                    if elem.get_text(strip=True):
                        content_parts.append(clean_content(elem))
            content = "\n".join(content_parts)

        # Si aucun bloc-formation n'a de <h2>, on ne traite que les <p>
        else:
            paragraphs = soup.find_all("p")
            content = "\n".join([
                clean_content(p) for p in paragraphs if p.get_text(strip=True)
            ])

    # Alerte en cas de contenu vide
    if not content.strip():
        print(f"[WARNING] Contenu vide pour : {url}")
        return []

    # On parse l'URL et on extrait les metadata pour le JSON
    parsed = urllib.parse.urlparse(url)
    site = parsed.netloc.replace("www.", "")
    category = extract_category(url)
    filiere = get_filierespecifique(url)

    # On supprime le footer
    content = content.replace(FOOTER_TEXT, "").strip()

    # On crée le JSON
    json_obj = {
        "url": url,
        "site": site,
        "category": category,
        "title": title,
        "filierespecifique": filiere,
        "datespecifique": "NA",
        "content": content,
    }

    # On normalise le titre
    filename = normalize_title(title)
    filepath = os.path.join(JSON_DOWNLOAD_DIR, filename)

    # Vérification de la pré-existence et du contenu du fichier
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            if existing_data == json_obj:
                print(f"[INFO] Fichier identique déjà présent : {filepath}")
                # On ne considère pas ce fichier comme nouveau
                # et on passe à la suite sans enregistrement.
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

    # On retourne les nouvelles URL trouvées sur la page
    return extract_new_urls(soup, url)

# ----------------------------------------------
# Fonction pour trouver les URL sur une page web
# ----------------------------------------------

def extract_new_urls(soup, url):
    
    # On extrait les nouvelles URL à partir d'une URL
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

    # On retourne les nouvelles URL
    return new_urls

# ---------------------------------------------------------
# Fonction de crawl qui parcourt toutes les URL de sa queue
# ---------------------------------------------------------

def crawl(start_url):
    
    # On crée une queue à partir de l'URL mère
    queue = deque([start_url])

    # On itère jusqu'à ne plus avoir d'URL dans la queue
    while queue:

        # Traitement de la queue
        current_url = queue.popleft()
        if current_url in visited_urls:
            continue
        print(f"[SCRAPING] Page : {current_url}")
        visited_urls.add(current_url)
        new_urls = scrape_page(current_url)
        for url in new_urls:
            if url not in visited_urls:
                queue.append(url)

        # Petite pause pour éviter de surcharger le serveur
        time.sleep(1)  

# -----------------------------------------------------------------------------
# Fonction principale de type 'if __name__ == "__main__":'
# ATTENTION : CETTE FONCTION N'EST PAS EXECUTEE AUTOMATIQUEMENT EN CAS D'IMPORT
# Cela est du au fait que le présent module (module_scrap_json.py) est importé
# dans l'outil de scrap global (../scraping_script.py) où il est utilisé
# Cette fonction ne sert donc qu'à tester ce module de manière indépendante
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    crawl(BASE_URL)
    print("\n[SCRAP TERMINÉ]")
    print(f"Pages visitées: {len(visited_urls)}")
    print(f"Nouveaux JSON enregistrés : {new_json_count}")

# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import os
import requests
from bs4 import BeautifulSoup
import re
import yaml

# Imports d'elements specifiques externes
from urllib.parse import urljoin, urlparse

# ------------------------------------------------------------------
# Chargement et récupération des paramètres de scrap depuis le .YAML
# ------------------------------------------------------------------

# Chargement
config_path = os.path.join(os.path.dirname(__file__), "../config_scrap.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Récupération
BASE_URL = config["BASE_URL"]
DOWNLOAD_DIR = config["PDF_DOWNLOAD_DIR"]
EXCLUDE_PREFIXES = config["PDF_EXCLUDE_PREFIXES"]
EXCLUDE_STRINGS = config["PDF_EXCLUDE_STRINGS"]
REPLACEMENTS = config["PDF_REPLACEMENTS_IN_FILE_NAMES"]

# ---------------------------
# Initialisation de variables
# ---------------------------

DOMAIN = urlparse(BASE_URL).netloc
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
visited_pages = set()
downloaded_pdfs = set()  # Ensemble des URLs déjà rencontrées (qu'elles aient été téléchargées ou déjà présentes)
new_download_count = 0   # Compteur des PDF réellement téléchargés pendant l'exécution

# ------------------------------------------------------------
# Fonction pour normaliser une URL en supprimant ses fragments
# ------------------------------------------------------------

def normalize_url(url):

    parsed = urlparse(url)
    normalized = parsed._replace(fragment="").geturl()
    return normalized

# ----------------------------------------------------------------
# Fonction déterminant s'il faut exclure une URL de celles à scrap
# ----------------------------------------------------------------

def should_exclude(url, exclude_substrings):

    # Exclusion en cas de préfixe interdit
    for prefix in EXCLUDE_PREFIXES:
        if url.startswith(prefix):
            return True

    # Exclusion en cas de présence de strings interdits
    parsed = urlparse(url)
    for substr in exclude_substrings:
        if substr in parsed.path:
            return True

    # Sinon, l'URL n'a pas à être exclue
    return False

# -------------------------------------------------
# Fonction gérant le téléchargement de fichiers PDF
# -------------------------------------------------

def download_pdf(pdf_url):
    
    # Variable globale pour garder le compte des téléchargements effectués
    global new_download_count

    # On évite les PDF déjà rencontrés
    if pdf_url in downloaded_pdfs:
        print(f"[INFO] PDF déjà rencontré : {pdf_url}")
        return

    # Récupération du nom de fichier et application des remplacements
    parsed_url = urlparse(pdf_url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        print(f"[WARNING] Impossible de déterminer le nom de fichier pour {pdf_url}.")
        return
    pattern = re.compile("|".join(map(re.escape, REPLACEMENTS.keys())))
    filename = pattern.sub(lambda match: REPLACEMENTS[match.group(0)], filename)
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    # Obtension de la taille du fichier PDF distant via une requête HEAD
    try:
        head_response = requests.head(pdf_url, timeout=10)
        head_response.raise_for_status()
        remote_size = int(head_response.headers.get("Content-Length", -1))
    except Exception as e:
        print(f"[WARNING] Impossible d'obtenir la taille du PDF via HEAD pour {pdf_url}: {e}")
        remote_size = -1

    # Si le fichier PDF courant existe déjà localement, on compare sa taille à celle du distant
    if os.path.exists(filepath):
        local_size = os.path.getsize(filepath)
        if remote_size != -1:
            if local_size == remote_size:
                print(f"[INFO] Fichier identique déjà présent : {filepath}")
                downloaded_pdfs.add(pdf_url)
                return
            else:
                print(f"[INFO] Fichier existant diffère en taille (local: {local_size} vs distant: {remote_size}). Téléchargement de la nouvelle version.")
        # Si la taille distante n'est pas disponible, on télécharge le PDF par prudence
        else:
            print(f"[INFO] Taille distante non disponible pour {pdf_url}. Téléchargement par précaution.")

    # On télécharge le PDF
    try:
        response = requests.get(pdf_url, stream=True, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Téléchargement du PDF {pdf_url} impossible: {e}")
        return
    print(f"[DOWNLOAD] Téléchargement de : {pdf_url}")
    try:
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        new_download_count += 1
        downloaded_pdfs.add(pdf_url)
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'écriture du fichier {filepath} : {e}")

# ------------------------------------------
# Fonction gérant le scraping d'une page web
# C'est une fonction récursive, donc chaque
# instance de scrape_page(url) en genere 
# d'autres qui ont leur propre exécution
# ------------------------------------------

def scrape_page(url):

    # On normalise l'URL et on vérifie qu'elle n'est ni déjà visitée, ni à éviter
    normalized_url = normalize_url(url)
    if normalized_url in visited_pages or should_exclude(normalized_url, EXCLUDE_STRINGS):
        return

    # Affichage du message et ajout aux pages visitées
    print(f"[SCRAPING] Page : {normalized_url}")
    visited_pages.add(normalized_url)

    # Requete pour accéder à la page
    try:
        response = requests.get(normalized_url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Impossible d'accéder à {normalized_url}: {e}")
        return
    
    # On parse la page avec BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # On trouve les références à d'autres pages sur la page courante
    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(normalized_url, href)
        full_url = normalize_url(full_url)

        # On évite les nouvelles URL problématiques
        if should_exclude(full_url, EXCLUDE_STRINGS):
            continue

        # On s'intéresse aux URL référençant des PDF
        if full_url.lower().endswith(".pdf"):
            if full_url in downloaded_pdfs:
                continue
            download_pdf(full_url)

        # Sinon (si la nouvelle URL trouvée ne contient pas de .PDF),
        # on lance une nouvelle instance de scrape_page() dessus
        else:
            parsed_link = urlparse(full_url)
            if parsed_link.netloc == DOMAIN:
                if full_url not in visited_pages:
                    scrape_page(full_url)

# -----------------------------------------------------------------------------
# Fonction principale de type 'if __name__ == "__main__":'
# ATTENTION : CETTE FONCTION N'EST PAS EXECUTEE AUTOMATIQUEMENT EN CAS D'IMPORT
# Cela est du au fait que le présent module (module_scrap_pdf.py) est importé
# dans l'outil de scrap global (../scraping_script.py) où il est utilisé
# Cette fonction ne sert donc qu'à tester ce module de manière indépendante
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    scrape_page(BASE_URL)
    print("\n[SCRAP TERMINÉ]")
    print(f"Pages visitées: {len(visited_pages)}")
    print(f"Nouveaux PDF téléchargés : {new_download_count}")

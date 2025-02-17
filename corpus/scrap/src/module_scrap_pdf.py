import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import yaml

# Configuration
# Charger la configuration à partir de config.yaml
config_path = os.path.join(os.path.dirname(__file__), "../config_scrap.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Récupération des paramètres depuis le YAML
BASE_URL = config["BASE_URL"]
DOWNLOAD_DIR = config["PDF_DOWNLOAD_DIR"]
EXCLUDE_PREFIXES = config["PDF_EXCLUDE_PREFIXES"]
EXCLUDE_STRINGS = config["PDF_EXCLUDE_STRINGS"]
REPLACEMENTS = config["PDF_REPLACEMENTS_IN_FILE_NAMES"]

DOMAIN = urlparse(BASE_URL).netloc
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
visited_pages = set()
downloaded_pdfs = set()  # Ensemble des URLs déjà rencontrées (qu'elles aient été téléchargées ou déjà présentes)
new_download_count = 0   # Compteur des PDF réellement téléchargés pendant l'exécution

def normalize_url(url):
    """
    Supprime le fragment d'une URL (tout ce qui suit '#') afin de normaliser l'URL.
    """
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="").geturl()
    return normalized

def should_exclude(url, exclude_substrings):
    """
    Exclut l'URL si elle commence par un des préfixes ou si le chemin de l'URL 
    contient l'une des chaînes spécifiées dans exclude_substrings.
    """
    # Exclusion par préfixe
    for prefix in EXCLUDE_PREFIXES:
        if url.startswith(prefix):
            return True

    # Exclusion par présence de chaînes dans le path
    parsed = urlparse(url)
    for substr in exclude_substrings:
        if substr in parsed.path:
            return True

    return False

def download_pdf(pdf_url):
    global new_download_count
    if pdf_url in downloaded_pdfs:
        print(f"[INFO] PDF déjà téléchargé ou rencontré : {pdf_url}")
        return

    try:
        response = requests.get(pdf_url, stream=True, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERREUR] Téléchargement du PDF {pdf_url} impossible: {e}")
        return

    parsed_url = urlparse(pdf_url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        print(f"[WARNING] Impossible de déterminer le nom de fichier pour {pdf_url}.")
        return

    # Appliquer les remplacements avec regex de manière concise
    pattern = re.compile("|".join(map(re.escape, REPLACEMENTS.keys())))
    filename = pattern.sub(lambda match: REPLACEMENTS[match.group(0)], filename)
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(filepath):
        print(f"[INFO] Fichier déjà présent : {filepath}")
        downloaded_pdfs.add(pdf_url)
        return

    print(f"[DOWNLOAD] Téléchargement de : {pdf_url}")
    try:
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        new_download_count += 1  # Incrémenter le compteur uniquement si le téléchargement est effectué
        downloaded_pdfs.add(pdf_url)
    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'écriture du fichier {filepath}: {e}")

def scrape_page(url):
    normalized_url = normalize_url(url)
    if normalized_url in visited_pages or should_exclude(normalized_url, EXCLUDE_STRINGS):
        return

    print(f"[SCRAPING] Page : {normalized_url}")
    visited_pages.add(normalized_url)

    try:
        response = requests.get(normalized_url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERREUR] Impossible d'accéder à {normalized_url}: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(normalized_url, href)
        full_url = normalize_url(full_url)

        if should_exclude(full_url, EXCLUDE_STRINGS):
            continue

        if full_url.lower().endswith(".pdf"):
            # Vérification avant d'appeler download_pdf
            if full_url in downloaded_pdfs:
                continue
            download_pdf(full_url)
        else:
            parsed_link = urlparse(full_url)
            if parsed_link.netloc == DOMAIN:
                if full_url not in visited_pages:
                    scrape_page(full_url)

if __name__ == "__main__":
    scrape_page(BASE_URL)
    print("\n[SCRAP TERMINÉ]")
    print(f"Pages visitées: {len(visited_pages)}")
    print(f"Nouveaux PDF téléchargés : {new_download_count}")

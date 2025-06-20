# -----------------------
# Imports des utilitaires
# -----------------------

import os
import time
import requests
import re
import json
import shutil
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, unquote
from PyPDF2 import PdfReader
from PyPDF2.generic import IndirectObject

from .scraper_utils import HEADERS, extract_urls_sitemap

# ------------------------------------
# Initialisation de variables globales
# ------------------------------------

visited_pages = set()             # Pages HTML analysées
new_download_count = 0            # Compteur de nouveaux PDF téléchargés

# -------------------------------------------------------------
# Chargement de la correspondance page -> PDF depuis un fichier
# -------------------------------------------------------------

def load_pdf_map(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# -------------------------------------------------------------
# Sauvegarde de la correspondance page -> PDF dans un fichier
# -------------------------------------------------------------

def save_pdf_map(pdf_map, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(pdf_map, f, ensure_ascii=False, indent=4)

# ------------------------------------
# Génère un nom de fichier pour un PDF
# ------------------------------------

def get_pdf_filename(pdf_url, site_config):

    # Extraction du nom de fichier à partir de l'url
    filename = os.path.basename(urlparse(pdf_url).path)
    filename = unquote(filename).replace(" ", "_")
    if not filename.lower().endswith(".pdf"):
        # Retirer toute extension incorrecte avant d'ajouter .pdf
        filename = re.sub(r"\.pdf[a-z]*$", "", filename, flags=re.IGNORECASE) + ".pdf"

    # Remplacements dans les noms de fichiers si définis dans la configuration
    replacements = site_config.get("PDF_REPLACEMENTS_IN_FILE_NAMES", {})
    if replacements:
        pattern = re.compile("|".join(map(re.escape, replacements.keys())))
        filename = pattern.sub(lambda match: replacements[match.group(0)], filename)

    return filename

# ---------------------------------------------
# Extraction des liens PDF depuis une page HTML
# ---------------------------------------------

def extract_pdf(url):

    # Liste pour stocker les liens PDF trouvés
    pdf_links = []
    try:

        # Requête HTTP pour récupérer le contenu de la page
        response = requests.get(url, timeout=10, headers=HEADERS)
        response.raise_for_status()

        # Parsing du contenu HTML avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche des balises <a> avec un attribut href
        for balise in soup.find_all('a', href=True):
            href = balise['href']

            # Si le lien contient ".pdf", on le considère comme un lien vers un fichier pdf
            if '.pdf' in href.lower():

                # Construction de l'url absolue
                if not href.endswith('.pdf'):
                    # Si le lien ne se termine pas par .pdf, on le corrige
                    href = re.sub(r'\.pdf[a-z]*$', '.pdf', href, flags=re.IGNORECASE)
                pdf_links.append(urljoin(url, href))

    except Exception as e:
        print(f"[ERREUR] Lecture échouée pour {url} ({e})")

    return pdf_links

# -----------------------------------------------------------------
# Téléchargement d’un fichier PDF s’il n’existe pas déjà localement
# -----------------------------------------------------------------

def download_pdf(filename, pdf_url, directory):

    # Compteur de nouveaux téléchargements
    global new_download_count

    # Vérification de l'existence du fichier
    file_path = os.path.join(directory, filename)
    if os.path.exists(file_path):
        print(f"[INFO] Déjà présent : {filename}")
        return True

    try:
        # Téléchargement du fichier PDF
        response = requests.get(pdf_url, stream=True, timeout=15, headers=HEADERS)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            f.write(response.content)

        # Incrémentation du compteur de nouveaux téléchargements
        new_download_count += 1
        print(f"[DOWNLOAD] Téléchargé : {filename}")
        return True

    except Exception as e:
        print(f"[ERREUR] Échec de téléchargement : {pdf_url} ({e})")

        # On supprime le fichier partiellement téléchargé s'il existe
        if os.path.exists(file_path):
            os.remove(file_path)
        return False

# -------------------------------------------------
# Extrait la date de dernière modification d’un PDF
# -------------------------------------------------

def get_pdf_metadata(pdf_path):

    try:
        # Ouvre le PDF et lit les métadonnées
        reader = PdfReader(pdf_path)
        info = reader.metadata

        # Titre
        raw_title = info.get('/Title')
        if isinstance(raw_title, IndirectObject):
            raw_title = raw_title.get_object()
        title = raw_title.strip() if isinstance(raw_title, str) else None

        # Dates dans les métadonnées PDF
        raw_date = info.get('/ModDate') or info.get('/CreationDate')
        if isinstance(raw_date, IndirectObject):
            raw_date = raw_date.get_object()
        lastmodif = None
        if isinstance(raw_date, str):
            match = re.search(r'D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', raw_date)
            if match:
                try:
                    lastmodif = datetime(int(match[1]), int(match[2]), int(match[3]), int(match[4]), int(match[5]), int(match[6])).isoformat()
                except ValueError:
                    lastmodif = None

        # Fallback si la date est toujours vide -> date du fichier sur le disque
        if not lastmodif:
            timestamp = os.path.getmtime(pdf_path)
            lastmodif = datetime.fromtimestamp(timestamp).isoformat()

        return {
            "title": title if title else os.path.basename(pdf_path),
            "lastmodif": lastmodif
        }
    
    except Exception as e:
        print(f"[ERREUR] Erreur extraction metadata pour {pdf_path} : {e}")
        return {
            "title": None,
            "lastmodif": None
        }
    
# -----------------------
# Définit le nom d’un PDF
# -----------------------

def clean_filename_title(filename):

    # Enlever l'extension
    name = os.path.splitext(filename)[0]

    # Remplacer tirets/underscores par espaces
    name = re.sub(r'[_\-]+', ' ', name)

    # Supprimer les suffixes techniques ou numériques non pertinents
    name = re.sub(r'\b(v(er)?(sion)?\.?\s?\d+(\.\d+)?|web|final|modif|officielle|version|diffusable|online|rev\d*)\b', '', name, flags=re.IGNORECASE)

    # Supprimer les groupes de chiffres sans intérêt (hors années 1900-2099)
    name = re.sub(r'\b(?!(19|20)\d{2})\d+\b', '', name)

    # Supprimer les espaces multiples
    name = re.sub(r'\s+', ' ', name).strip()

    # Mettre une majuscule au premier mot
    if name:
        name = name[0].upper() + name[1:]

    return name


def compute_file_hash(path):
    """Calcule le hash SHA256 d'un fichier PDF"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        print(f"[ERREUR] Échec du calcul de hash pour {path} : {e}")
        return None

# -----------------------------------------------------
# Scrape les PDFs d’un site web à partir de son sitemap
# -----------------------------------------------------

def scrape_page(site_config):

    # Pages visitées et compteur de nouveaux téléchargements
    global visited_pages, new_download_count

    # Réinitialisation des compteurs à chaque appel
    visited_pages.clear()
    new_download_count = 0

    # Récupération des paramètres de configuration du site
    base_url = site_config["BASE_URL"]
    sitemap_url = site_config["SITEMAP_URL"]
    directory_pdfs = site_config["PDF_DOWNLOAD_DIR"]
    exclusions = site_config.get("EXCLUDE_URL_KEYWORDS", [])

    # Définition de la date de dernière modification
    if site_config.get("LAST_MODIFIED_DATE") != None:
        limit_date = datetime.strptime(site_config["LAST_MODIFIED_DATE"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        limit_date = None

    # Création du dossier de téléchargement et du dossier d'archives s'ils n'existent pas
    os.makedirs(directory_pdfs, exist_ok=True)
    archive_dir = os.path.join(directory_pdfs, "_archives")
    os.makedirs(archive_dir, exist_ok=True)

    # Extraction des URLs du sitemap et filtrage
    urls_and_dates = extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date)
    urls_pages = [u for u, _ in urls_and_dates]
    urls_lastmod = {u: d for u, d in urls_and_dates}
    print(f"🔗 {len(urls_pages)} pages HTML à analyser")

    # Chargement de la correspondance page -> PDF
    pdf_map_file = os.path.join(os.path.dirname(directory_pdfs), "pdf_map.json")
    pdf_map = load_pdf_map(pdf_map_file)
    updated_pdf_map = {}

    # Liste des pdfs rencontrés lors du scraping
    seen_pdf_filenames = set()

    # Parcours des URLs extraites
    for i, url in enumerate(urls_pages):

        # Extraction des pdfs et ajout à l'ensemble des pages visitées
        visited_pages.add(url)
        print(f"[{i+1}/{len(urls_pages)}] {url}")
        pdfs = extract_pdf(url)

        # Téléchargement des PDF extraits
        for pdf in pdfs:
            filename = get_pdf_filename(pdf, site_config)
            if filename not in seen_pdf_filenames:
                seen_pdf_filenames.add(filename)
                if download_pdf(filename, pdf, directory_pdfs):
                
                    file_path = os.path.join(directory_pdfs, filename)
                    meta = get_pdf_metadata(file_path)
                    updated_pdf_map[filename] = {
                        "title": meta["title"] or filename,
                        "title_2": clean_filename_title(filename),
                        "url": url,
                        "last_modified": meta["lastmodif"] or urls_lastmod.get(url, None),
                        "hash": compute_file_hash(file_path),
                        "scraped_at": datetime.now().isoformat()
                    }
        time.sleep(0.5)

    # Archivage des PDF non rencontrés lors du scraping
    old_filenames_from_modified_pages = {f for f, page in pdf_map.items() if page in urls_pages}
    outdated_pdfs = old_filenames_from_modified_pages - seen_pdf_filenames
    for outdated in outdated_pdfs:
        src_path = os.path.join(directory_pdfs, outdated)
        dest_path = os.path.join(archive_dir, outdated)
        try:
            shutil.move(src_path, dest_path)
            print(f"[ARCHIVE] Ancien fichier déplacé : {outdated}")
            pdf_map.pop(outdated, None)
        except Exception as e:
            print(f"[ERREUR] Échec de l'archivage de {outdated} : {e}")

    pdf_map.update(updated_pdf_map)
    save_pdf_map(pdf_map, pdf_map_file)


# -----------------------
# Imports des utilitaires
# -----------------------

import re
import json
import time
import unicodedata
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup, Tag
from datetime import datetime, timezone

from .scraper_utils import PROGRESS_DIR, HEADERS, extract_urls_sitemap, save_progress, clear_progress

# ------------------------------------
# Initialisation de variables globales
# ------------------------------------

visited_pages = set()             # Pages HTML analysées
new_json_count = 0            # Compteur de nouveaux JSON téléchargés

# -----------------------------------------------------------------
# Génère un nom de fichier à partir du titre de la page et de l'URL
# -----------------------------------------------------------------

def normalize_filename(title, url, download_dir):

    # Normaliser le titre
    title = title.replace('\u00A0', ' ').strip()
    title_norm = title.replace("œ", "oe").replace("Œ", "OE")
    nfkd_form = unicodedata.normalize('NFKD', title_norm)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8').lower()
    title_norm = re.sub(r'\W+', '_', only_ascii).strip('_')

    # Étape 2 : nom initial
    base_filename = f"{title_norm}.json"
    base_path = download_dir / base_filename

    # Étape 3 : vérifier s'il y a déjà un fichier du même nom
    if base_path.exists():
        try:
            with open(base_path, "r", encoding="utf-8") as f:
                existing = json.load(f)

            # Si même URL, on peut écraser
            if existing.get("url") == url:
                return base_filename
            # Sinon, nom alternatif avec suffixe path
            else:
                parsed = urlparse(url)
                path_suffix = parsed.path.strip("/").replace("/", "_")
                fallback_filename = f"{title_norm}_{path_suffix}.json"
                return fallback_filename

        # En cas d’erreur de lecture : fallback safe
        except Exception:
            parsed = urlparse(url)
            path_suffix = parsed.path.strip("/").replace("/", "_")
            return f"{title_norm}_{path_suffix}.json"

    return base_filename

# --------------------------------
# Détermine le titre de la page HTML
# --------------------------------

def extract_title(soup, url):

    # On essaie de trouver h1
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True).replace('\u00A0', ' ')
    
    # Sinon on essaie de trouver title
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True).replace('\u00A0', ' ')
    
    # Sinon une partie de l'URL
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split('/') if part]
    return parts[-1] if parts else "no_title"

# ---------------------------------------
# Calcule le hash SHA-256 d'un objet JSON
# ---------------------------------------

def hash_json(obj):
    filtered = {k: v for k, v in obj.items() if k not in ["lastmodif", "hash", "scraped_at"]}
    return hashlib.sha256(json.dumps(filtered, sort_keys=True).encode('utf-8')).hexdigest()

# -----------------------------------------
# Archive les JSON dont l'url n'existe plus
# -----------------------------------------

def archive_old_jsons(download_dir, archive_dir, urls):

    # On regarde les fichiers JSON existants dans le dossier de téléchargement
    for filepath in download_dir.iterdir():

        if not filepath.is_file():
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Archive si l'URL du JSON n'est pas dans la liste des URLs du site lors du scraping
            if data["url"] not in urls:
                archive_path = archive_dir / filepath.name
                filepath.rename(archive_path)
                print(f"[ARCHIVE] Ancien fichier déplacé : {filepath.name}")

        except Exception as e:
            print(f"[ERREUR] Échec de lecture ou d'archivage de {filepath} : {e}")

# -------------------------------------------------
# Nettoie le contenu HTML pour en extraire le texte
# -------------------------------------------------

def extract_main_content(soup):

    parts = []

    # 1. Supprimer les balises globalement inutiles
    def is_block_to_remove(tag):
        if not isinstance(tag, Tag):
            return False

        keywords_header = ["header", "nav", "menu", "topbar"]
        keywords_footer = ["footer", "bottom", "copyright"]
        keywords_cookie = ["cookie", "privacy", "consent", "gdpr"]
        keywords_accessibility = ["accessibilité", "contraste", "taille de police", "cmplz"]
        keywords_remove = keywords_header + keywords_footer + keywords_cookie + keywords_accessibility + [
            "bloc-formation", "liste-anchor", "anchor-link", "block-brochureetcandidature"
        ]
        keywords_keep = [
            "page-header", "info", "banner", "header-bloc-info", "header-info", "formation-header",
            "field--item", "description", "content", "bloc", "section", "main", "region-content"
        ]

        id_class = " ".join(tag.get("class", []) + [tag.get("id", "")]).lower()

        if tag.name in ["html", "body"]:
            return False

        if any(k in id_class for k in keywords_keep):
            return False

        if tag.name in ["header", "nav", "footer", "aside"]:
            return True

        if any(k in id_class for k in keywords_remove):
            return True

        return False

    for tag in soup.find_all(is_block_to_remove):
        tag.decompose()

    # 2. Définir la zone de contenu principale
    article = soup.find("article")
    container = article if article else soup.body
    if container is None:
        return ""
    
    # 3. Traitement spécifique : h1 et h4 de l'en-tête d'article
    header_block = soup.select_one("div.page-header")
    if header_block:
        main_title = header_block.find("h1")
        if main_title:
            parts.append(f"# {main_title.get_text(strip=True)}")

        author_date = header_block.find("h4", class_="author")
        if author_date:
            text = author_date.get_text(strip=True)
            if text:
                parts.append(f"*{text}*")

    # ✅ Cas spécial : domaine de formations Polytech
    formation_links = soup.select("a.col-sm-4")
    if formation_links:
        for link in formation_links:
            title_tag = link.select_one(".title")
            title = title_tag.get_text(strip=True)
            parts.append(title)



    # 3. Traitement spécifique : h1 ou .banner
    title_tag = soup.select_one("h1.header-info-title")
    if title_tag:
        parts.append(f"# {title_tag.get_text(strip=True)}")

    banner_section = soup.select_one(".banner")
    if banner_section:
        banner_title = banner_section.find("h2")
        if banner_title:
            parts.append(f"## {banner_title.get_text(strip=True)}")
        for p in banner_section.select(".description p"):
            text = p.get_text(strip=True)
            if text:
                parts.append(text)

    # 4. Fonction récursive pour parcourir tous les enfants
    def process_tag(tag):
        if not isinstance(tag, Tag):
            return

        if tag.name == "h1":
            text = tag.get_text(strip=True)
            if text:
                parts.append(f"# {text}")
            return

        if "bloc-stage" in (tag.get("class") or []):
            title = tag.select_one(".stage-title")
            if title:
                parts.append(f"### {title.get_text(strip=True)}")
            description = tag.select_one(".stage-description p")
            if description:
                parts.append(description.get_text(strip=True))
            duration = tag.select_one(".stage-duree")
            if duration:
                parts.append(duration.get_text(strip=True))
            return
        

        if tag.name == "span" and tag.find_parent(class_="header-info"):
            field_items = tag.select(".field--item")
            if field_items:
                for item in field_items:
                    parts.append(f"- {item.get_text(strip=True)}")
            else:
                label = tag.find("label")
                if label:
                    text = label.get_text(strip=True)
                    if text:
                        parts.append(f"- {text}")
            return

        if tag.name == "span" and "doughnut-chart-text" in (tag.get("class") or []):
            text = tag.get_text(strip=True)
            if text:
                parts.append(text)
            return

        if tag.name == "div" and "activite-progress-bloc" in (tag.get("class") or []):
            pct_tag = tag.select_one(".progress-left-text strong")
            label_tag = tag.select_one(".progress-right-text p")
            if pct_tag and label_tag:
                parts.append(f"- {pct_tag.get_text(strip=True)} {label_tag.get_text(strip=True)}")
            return

        if tag.name in ["h2", "h3", "h4", "h5", "p", "ul", "ol"]:
            text = tag.get_text(strip=True)
            if not text:
                return
            if tag.name in ["h2", "h3", "h4", "h5"]:
                level = int(tag.name[1])
                parts.append(f"{'#' * level} {text}")
            elif tag.name == "p":
                parts.append(text)
            elif tag.name == "ul":
                for li in tag.find_all("li", recursive=False):
                    parts.append(f"- {li.get_text(strip=True)}")
            elif tag.name == "ol":
                for i, li in enumerate(tag.find_all("li", recursive=False), start=1):
                    parts.append(f"{i}. {li.get_text(strip=True)}")
            return

        # Cas des divs avec texte direct
        if tag.name == "div":
            direct_text = tag.get_text(strip=True)
            has_tags = any(isinstance(c, Tag) for c in tag.contents)
            if direct_text and not has_tags:
                parts.append(direct_text)
                return  # on évite les doublons, div purement textuelle
            # Sinon, on descend dans les enfants

        # Continuer la descente dans les enfants
        for child in tag.children:
            if isinstance(child, Tag):
                process_tag(child)

    # 5. Lancement du traitement depuis le container principal
    for child in container.children:
        if isinstance(child, Tag):
            process_tag(child)


    return "\n".join(parts).replace('\u00A0', ' ').strip()


# --------------------------------
# Fonction gérant le scraping JSON
# --------------------------------

def crawl(site_config):

    site_name = site_config["NAME"].replace(" ", "_").lower()
    clear_progress(site_name, "2/2 - Récupération des pages web")

    # Pages visitées et compteur de nouveaux JSON
    global visited_pages, new_json_count

    # Réinitialisation des compteurs à chaque appel
    visited_pages.clear()
    new_json_count = 0

    # Récupération des paramètres de configuration du site
    base_url = site_config["BASE_URL"]
    sitemap_url = site_config["SITEMAP_URL"]
    download_dir = Path(site_config["JSON_DOWNLOAD_DIR"])
    exclusions = site_config.get("EXCLUDE_URL_KEYWORDS", [])

    start = time.time()

    # Définition de la date de dernière modification
    if site_config.get("LAST_MODIFIED_DATE") is not None:
        limit_date = datetime.fromisoformat(site_config["LAST_MODIFIED_DATE"])
        if limit_date.tzinfo is None:
            limit_date = limit_date.replace(tzinfo=timezone.utc)
    else:
        limit_date = None

    # Création du dossier de téléchargement s'il n'existe pas
    download_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = download_dir / "_archives"
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Extraction des URLs du sitemap et filtrage
    all_urls_and_dates = extract_urls_sitemap(sitemap_url, base_url, exclusions, None)
    all_urls = [u for u, _ in all_urls_and_dates]
    urls_and_dates = extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date)
    urls_pages = [u for u, _ in urls_and_dates]
    urls_lastmod = {u: d for u, d in urls_and_dates}
    total_pages = len(urls_pages)
    print(f"🔗 {total_pages} pages HTML à analyser")

    # Chargement des JSON déjà présents, indexés par URL
    existing_by_url = {}
    for filepath in download_dir.glob("*.json"):

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                url_ = data.get("url")
                if url_:
                    existing_by_url[url_] = {
                        "filepath": filepath,
                        "data": data
                    }
        except Exception as e:
            print(f"[WARNING] Impossible de lire {filepath} : {e}")

    # Parcours des URLs extraites
    for i, url in enumerate(urls_pages):

        visited_pages.add(url)
        print(f"[{i+1}/{len(urls_pages)}] {url}")

        save_progress(site_name, i + 1, total_pages, f"2/2 - Récupération des pages web ({i+1}/{total_pages})")

        # Requête HTTP pour récupérer le contenu de la page
        try:
            response = requests.get(url, timeout=10, headers=HEADERS)
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR] Requête échouée pour {url} : {e}")
            continue

        # Analyse HTML et extraction du titre et du contenu
        soup = BeautifulSoup(response.text, "html.parser")
        title = extract_title(soup, url)
        content = extract_main_content(soup)
        if not content:
            print(f"[WARNING] Contenu vide pour : {url}")
            continue
    
        # Analyse de l'URL pour extraire le site et la catégorie
        parsed = urlparse(url)
        site = parsed.netloc.replace("www.", "")
        parts = [p for p in parsed.path.split('/') if p]
        category = parts[1] if len(parts) >= 2 else (parts[0] if parts else "NA")

        # Création de l'objet JSON final
        now_date = datetime.now(timezone.utc).isoformat()
        json_obj = {
            "url": url,
            "site": site,
            "category": category,
            "title": title,
            "hash" : "NA",
            "last_modified": "NA",
            "scraped_at": now_date,
            "content": content
        }

        existing_entry = existing_by_url.get(url)
        if existing_entry:
            existing_data = existing_entry["data"]
            existing_path = existing_entry["filepath"]
            filepath = existing_path
            json_obj["last_modified"] = existing_data.get("last_modified")

            if hash_json(existing_data) == hash_json(json_obj):
                print(f"[INFO] Fichier identique déjà présent : {filepath}")
                continue
            else:
                print(f"[INFO] Mise à jour du fichier existant : {filepath}")

        else:
            # Normalisation du nom de fichier
            filename = normalize_filename(title, url, download_dir)
            filepath = download_dir / filename

        # Écriture du nouveau fichier JSON
        try:
            lastmodif = urls_lastmod.get(url)
            if lastmodif:
                json_obj["last_modified"] = lastmodif.isoformat()
            else:
                json_obj["last_modified"] = "NA"
            json_obj["hash"] = hash_json(json_obj)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, ensure_ascii=False, indent=4)
            new_json_count += 1
            print(f"[DOWNLOAD] {filepath}")

        except Exception as e:
            print(f"[ERREUR] Écriture échouée de {filepath} : {e}")

        # Pause pour éviter de surcharger le serveur
        time.sleep(0.5)
    
    end = time.time()
    print(f"duration pas parallélisée = {end-start}")


    # Archivage des anciens JSON
    if all_urls:
        archive_old_jsons(download_dir, archive_dir, all_urls)
    else:
        print("[INFO] Archivage désactivé : aucune URL récupérée sur le site (site inaccessible ?)")    

    save_progress(site_name, total_pages, total_pages, "2/2 - Scraping terminé")
   

def crawl_test(url_test):

    # Pages visitées et compteur de nouveaux JSON
    global visited_pages, new_json_count

    # Réinitialisation des compteurs à chaque appel
    visited_pages.clear()
    new_json_count = 0

    # Création du dossier de téléchargement s'il n'existe pas
    download_dir = Path(__file__).parent / "test"
    download_dir.mkdir(parents=True, exist_ok=True)

    # Requête HTTP pour récupérer le contenu de la page
    try:
        response = requests.get(url_test, timeout=10, headers=HEADERS)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"[ERREUR] Requête échouée pour {url_test} : {e}")

    # Analyse HTML et extraction du titre et du contenu
    soup = BeautifulSoup(response.text, "html.parser")
    title = extract_title(soup, url_test)
    content = extract_main_content(soup)
    if not content:
        print(f"[WARNING] Contenu vide pour : {url_test}")

    # Analyse de l'URL pour extraire le site et la catégorie
    parsed = urlparse(url_test)
    site = parsed.netloc.replace("www.", "")
    parts = [p for p in parsed.path.split('/') if p]
    category = parts[1] if len(parts) >= 2 else (parts[0] if parts else "NA")

    # Création de l'objet JSON final
    now_date = datetime.now(timezone.utc).isoformat()
    json_obj = {
        "url": url_test,
        "site": site,
        "category": category,
        "title": title,
        "hash" : "NA",
        "last_modified": "NA",
        "scraped_at": now_date,
        "content": content
    }


    # Normalisation du nom de fichier
    filename = normalize_filename(title, url_test, download_dir)
    filepath = download_dir / filename

    # Écriture du nouveau fichier JSON
    try:
        json_obj["last_modified"] = "NA"
        json_obj["hash"] = hash_json(json_obj)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=4)
        new_json_count += 1
        print(f"[DOWNLOAD] {filepath}")

    except Exception as e:
        print(f"[ERREUR] Écriture échouée de {filepath} : {e}")

    # Pause pour éviter de surcharger le serveur
    time.sleep(0.5)
    

if __name__ == "__main__":
    crawl_test("https://www.polytech-reseau.org/12-domaines-de-formation/")

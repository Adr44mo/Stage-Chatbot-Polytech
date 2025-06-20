# -----------------------
# Imports des utilitaires
# -----------------------

import os
import re
import json
import time
import unicodedata
import hashlib
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup, Tag
from datetime import datetime, timezone

from .scraper_utils import HEADERS, extract_urls_sitemap

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
    base_path = os.path.join(download_dir, base_filename)

    # Étape 3 : vérifier s'il y a déjà un fichier du même nom
    if os.path.exists(base_path):
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
""" 
# -------------------------------------------------
# Nettoie le contenu HTML pour en extraire le texte
# -------------------------------------------------

def clean_content(soup):

    # Supprime les balises inutiles
    tags_to_remove = ["script", "style", "img", "video", "iframe", "object", "embed", "input", "label", "button", "header", "topbar", "menu", "navigation", "footer", "nav", "aside", "form"]
    for tag in soup(tags_to_remove):
        tag.decompose()

    # Remplace les liens par leur texte
    for a in soup.find_all("a"):
        a.replace_with(a.get_text())
    
    output = []

    def handle_tag(tag):
        if tag.name in ["h1", "h2", "h3", "h4"]:
            level = int(tag.name[1])
            output.append(f"{'#' * level} {tag.get_text(strip=True)}")
        elif tag.name == "p":
            text = tag.get_text(strip=True)
            if text:
                output.append(text)
        elif tag.name == "ul":
            for li in tag.find_all("li", recursive=False):
                output.append(f"- {li.get_text(strip=True)}")
        elif tag.name == "ol":
            for i, li in enumerate(tag.find_all("li", recursive=False), start=1):
                output.append(f"{i}. {li.get_text(strip=True)}")

    # Balises que l'on veut extraire dans l'ordre d'apparition
    for tag in soup.body.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol"], recursive=True):
        handle_tag(tag)

    return "\n\n".join(output)
# -------------------------------------------
# Détecte le header du site pour le supprimer
# -------------------------------------------

def detect_headers(soup):

    candidates = []
    candidates.extend(soup.find_all("header"))

    keywords = ["header", "topbar", "nav", "navigation", "menu"]

    def is_header_like(tag):
        id_match = any(k in (tag.get("id", "")).lower() for k in keywords)
        class_match = any(k in "".join(tag.get("class", [])).lower() for k in keywords)
        return tag.name in ["div", "section", "nav"] and (id_match or class_match)
    
    candidates.extend(soup.find_all(is_header_like))
    
    # Nettoie et déduplique le texte extrait
    seen_ids = set()
    headers = []
    for tag in candidates:
        if id(tag) not in seen_ids:
            seen_ids.add(id(tag))
            headers.append(tag)

    return headers

# -------------------------------------------
# Détecte le footer du site pour le supprimer
# -------------------------------------------

def detect_footers(soup):

    candidates = []
    candidates.extend(soup.find_all("footer"))

    keywords = ["footer", "bottom", "copyright"]

    def is_footer_like(tag):
        id_match = any(k in (tag.get("id", "")).lower() for k in keywords)
        class_match = any(k in "".join(tag.get("class", [])).lower() for k in keywords)
        return tag.name in ["div", "section", "nav"] and (id_match or class_match)

    candidates.extend(soup.find_all(is_footer_like))

    # Nettoie et déduplique le texte extrait
    seen_ids = set()
    footers = []
    for tag in candidates:
        if id(tag) not in seen_ids:
            seen_ids.add(id(tag))
            footers.append(tag)

    return footers

# -------------------------------------------------
# Détecte la bannière des cookies pour la supprimer
# -------------------------------------------------

def detect_cookie_banner(soup):

    keywords = ["cookie", "privacy", "consent", "gdpr", "manage"]
    button_texts = ["accepter", "accept", "refuser", "reject", "continuer", "close"]

    candidates = []
    for tag in soup.find_all(['div', 'section', 'aside']):
        text = tag.get_text(separator=' ').lower()
        buttons = tag.find_all(['button', 'a'])
        btn_texts = [b.get_text(separator=' ').lower() for b in buttons]

        # Compte les mots-clés présents
        keyword_matches = sum(1 for k in keywords if k in text)
        has_button_text = any(any(bt in btxt for bt in button_texts) for btxt in btn_texts)

        # Nouveau critère combiné
        if keyword_matches >= 2 or (keyword_matches >= 1 and has_button_text):
            candidates.append(tag)

    return candidates

# -----------------------------------------------------
# Détecte la bannière d'accessibilité pour la supprimer
# -----------------------------------------------------

def detect_accessibility_tools(soup):
    keywords = ["accessibilité", "outil d’accessibilité", "outil d'accessibilité", "contraste", "taille de police"]

    candidates = []
    for tag in soup.find_all(['div', 'section', 'aside', 'nav']):
        text = tag.get_text(separator=' ').lower()
        if any(k in text for k in keywords):
            candidates.append(tag)

    return candidates """

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
    for filename in os.listdir(download_dir):

        filepath = os.path.join(download_dir, filename)
        if not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Archive si l'URL du JSON n'est pas dans la liste des URLs du site lors du scraping
            if data["url"] not in urls:
                archive_path = os.path.join(archive_dir, filename)
                os.rename(filepath, archive_path)
                print(f"[ARCHIVE] Ancien fichier déplacé : {filename}")

        except Exception as e:
            print(f"[ERREUR] Échec de lecture ou d'archivage de {filepath} : {e}")

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


""" def extract_main_content(soup):

    parts = []
    # 1. Supprimer les balises globalement inutiles (menu, header, footer, aside, cookie banner...)
    def is_block_to_remove(tag):

        if not isinstance(tag, Tag):
            return False
        
        keywords_header = ["header", "nav", "menu", "topbar"]
        keywords_footer = ["footer", "bottom", "copyright"]
        keywords_cookie = ["cookie", "privacy", "consent", "gdpr"]
        keywords_accessibility = ["accessibilité", "contraste", "taille de police", "cmplz"]
        keywords_remove = keywords_header + keywords_footer + keywords_cookie + keywords_accessibility + ["bloc-formation", "liste-anchor", "anchor-link", "block-brochureetcandidature"]
        keywords_keep = ["page-header", "info", "banner", "header-bloc-info", "header-info", "formation-header", "header-info", "field--item", "description", "content", "bloc", "section", "main", "region-content"]

        id_class = " ".join(tag.get("class", []) + [tag.get("id", "")]).lower()

        # Ne jamais supprimer body ou html
        if tag.name in ["html", "body"]:
            return False

        # Si la classe/id contient un mot à garder, on ne supprime pas ce bloc
        if any(k in id_class for k in keywords_keep):
            return False

        # Test si tag est clairement un header/footer/menu
        if tag.name in ["header", "nav", "footer", "aside"]:
            return True
        
        if any(k in id_class for k in keywords_remove):
            return True
        
        return False

    for tag in soup.find_all(is_block_to_remove):
        print("[SUPPRIMÉ]", getattr(tag, "name", "???"), tag.get("class", "—") if tag and tag.attrs else "—", tag.get("id", "—") if tag and tag.attrs else "—", tag.get_text(strip=True)[:80] if tag else "—")
        tag.decompose()

    # 2. Chercher le contenu principal

    # Si il y a une balise <article>, on prend son contenu
    article = soup.find("article")
    container = article if article else soup.body
    if container is None:
        return ""  # ou log un avertissement et retourne une chaîne vide

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

    # Ici on va parcourir **tous les enfants directs et leurs descendants en ordre**, 
    # mais dès qu'on détecte un bloc-stage, on le traite en entier, puis on continue.

    def process_tag(tag):

        # Nouveau : détecter tout <h1> générique
        if tag.name == "h1":
            text = tag.get_text(strip=True)
            if text:
                parts.append(f"# {text}")
            return
        
        # Si on tombe sur un bloc-stage, on l'extrait puis on ne traite pas ses enfants (pour éviter doublons)
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
            return  # stop ici, pas besoin de traiter descendants, déjà fait
        
        # Gestion des spans dans .header-info
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
        
        # NOUVEAU : gestion des chiffres embauche
        if tag.name == "span" and "doughnut-chart-text" in (tag.get("class") or []):
            text = tag.get_text(strip=True)
            if text:
                parts.append(text)
            return
        
        # Gestion des secteurs d'activités
        if tag.name == "div" and "activite-progress-bloc" in (tag.get("class") or []):
            # Trouver le pourcentage dans progress-left-text
            pct_tag = tag.select_one(".progress-left-text strong")
            # Trouver le texte dans progress-right-text p
            label_tag = tag.select_one(".progress-right-text p")
            if pct_tag and label_tag:
                parts.append(f"- {pct_tag.get_text(strip=True)} {label_tag.get_text(strip=True)}")
            return

        # Sinon, on regarde si c'est une balise qu'on veut récupérer
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
        
        # Si c'est un <div> avec juste du texte
        if tag.name == "div":
            direct_text = tag.get_text(strip=True)
            if direct_text and not any(isinstance(c, Tag) for c in tag.contents):
                parts.append(direct_text)
                return

        # Pour les autres balises, on continue à parcourir leurs enfants
        for child in tag.children:
            if isinstance(child, Tag):
                process_tag(child)

    # Lancement du traitement depuis le container
    for child in container.children:
        if isinstance(child, Tag):
            process_tag(child)

    return "\n".join(parts).replace('\u00A0', ' ').strip() """

# --------------------------------
# Fonction gérant le scraping JSON
# --------------------------------

def crawl(site_config):

    # Pages visitées et compteur de nouveaux JSON
    global visited_pages, new_json_count

    # Réinitialisation des compteurs à chaque appel
    visited_pages.clear()
    new_json_count = 0

    # Récupération des paramètres de configuration du site
    base_url = site_config["BASE_URL"]
    sitemap_url = site_config["SITEMAP_URL"]
    download_dir = site_config["JSON_DOWNLOAD_DIR"]
    exclusions = site_config.get("EXCLUDE_URL_KEYWORDS", [])

    # Définition de la date de dernière modification
    if site_config.get("LAST_MODIFIED_DATE") is not None:
        limit_date = datetime.strptime(site_config["LAST_MODIFIED_DATE"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        limit_date = None

    # Création du dossier de téléchargement s'il n'existe pas
    os.makedirs(download_dir, exist_ok=True)
    archive_dir = os.path.join(download_dir, "_archives")
    os.makedirs(archive_dir, exist_ok=True)

    # Extraction des URLs du sitemap et filtrage
    all_urls_and_dates = extract_urls_sitemap(sitemap_url, base_url, exclusions, None)
    all_urls = [u for u, _ in all_urls_and_dates]
    urls_and_dates = extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date)
    urls_pages = [u for u, _ in urls_and_dates]
    urls_lastmod = {u: d for u, d in urls_and_dates}
    print(f"🔗 {len(urls_pages)} pages HTML à analyser")

    # Chargement des JSON déjà présents, indexés par URL
    existing_by_url = {}
    for filename in os.listdir(download_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(download_dir, filename)
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

    """ # Détection initiale (uniquement sur la première page)
    reference_blocks_html = {
        "headers": [],
        "footers": [],
        "cookies": [],
        "accessibility": []
    } """

    """ # Détection des headers et footers du site
    if urls_pages:
        try:
            res = requests.get(urls_pages[0], timeout=10, headers=HEADERS)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            # On stocke le HTML brut (string) des blocs détectés
            reference_blocks_html["headers"] = [str(tag) for tag in detect_headers(soup)]
            reference_blocks_html["footers"] = [str(tag) for tag in detect_footers(soup)]
            reference_blocks_html["cookies"] = [str(tag) for tag in detect_cookie_banner(soup)]
            reference_blocks_html["accessibility"] = [str(tag) for tag in detect_accessibility_tools(soup)]
            print("\n=== HEADER DÉTECTÉ ===")
            for h in reference_blocks_html["headers"]:
                print(h)
            print("======================\n")


        except requests.exceptions.RequestException as e:
            print(f"[ERREUR] Impossible d'analyser la première page ({urls_pages[0]}) pour détecter les headers/footers : {e}")
 """
    # Parcours des URLs extraites
    for i, url in enumerate(urls_pages):

        visited_pages.add(url)
        print(f"[{i+1}/{len(urls_pages)}] {url}")

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
        json_obj = {
            "url": url,
            "site": site,
            "category": category,
            "title": title,
            "hash" : "NA",
            "last_modified": "NA",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "content": content
        }

        existing_entry = existing_by_url.get(url)
        if existing_entry:
            existing_data = existing_entry["data"]
            existing_path = existing_entry["filepath"]

            json_obj["last_modified"] = existing_data.get("last_modified")

            if hash_json(existing_data) == hash_json(json_obj):
                print(f"[INFO] Fichier identique déjà présent : {filepath}")
                continue
            else:
                print(f"[INFO] Mise à jour du fichier existant : {filepath}")
                filepath = existing_path

        else:
            # Normalisation du nom de fichier
            filename = normalize_filename(title, url, download_dir)
            filepath = os.path.join(download_dir, filename)

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

    # Archivage des anciens JSON
    archive_old_jsons(download_dir, archive_dir, all_urls)

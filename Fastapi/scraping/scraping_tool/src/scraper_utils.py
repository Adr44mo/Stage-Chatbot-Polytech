# -----------------------
# Imports des utilitaires
# -----------------------

import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ---------------------------------
# User-agent pour les requêtes HTTP
# ---------------------------------
HEADERS = {
    "User-Agent": "PolytechScraper/1.0 (+https://github.com/Adr44mo/Stage-Chatbot-Polytech)"
}

# --------------------------------------
# Filtrage des URLs selon les exclusions
# --------------------------------------

def is_excluded(url, exclusions):

    return any(keyword in url for keyword in exclusions)

# ---------------------------------------
# Correction des préfixes URL incohérents
# ---------------------------------------

def correct_url_prefix(urls, correct_prefix):

    first_url = urls[0][0] if isinstance(urls[0], tuple) else urls[0]
    parsed_first = urlparse(first_url)
    first_prefix = f"{parsed_first.scheme}://{parsed_first.netloc}"

    # On teste uniquement la première url car s'il y a un problème de préfixe, il est généralisé
    if first_prefix != correct_prefix:
        #print(f"[INFO] Correction du préfixe des URLs : remplacement de {first_prefix} par {correct_prefix}")
        new_urls = []
        for item in urls:
            url = item[0] if isinstance(item, tuple) else item
            path_and_more = url[len(first_prefix):]
            corrected_url = correct_prefix + path_and_more
            if isinstance(item, tuple):
                new_urls.append((corrected_url, item[1]))
            else:
                new_urls.append(corrected_url)
    
        return new_urls
    
    return urls

# ----------------------------------------------
# Extraction récursive des URLs d’un sitemap XML
# ----------------------------------------------

def extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date):

    # Liste des urls extraites
    urls = []
    try:

        # Requête HTTP pour récupérer le contenu du sitemap
        response = requests.get(sitemap_url, timeout=10, headers=HEADERS)
        response.raise_for_status()
        
        # Décoder et nettoyer le contenu
        content = response.content.decode('utf-8', errors='ignore')

        # Trouver la première déclaration XML valide
        xml_start = content.find('<?xml')
        if xml_start > 0:
            content = content[xml_start:]  # On supprime tout ce qui précède le XML

        # Parsing du contenu XML avec BeautifulSoup
        soup = BeautifulSoup(content, 'xml')

        # Sitemap index : liste de sitemaps
        if soup.find('sitemapindex'):
            for sitemap in soup.find_all('sitemap'):
                loc = sitemap.loc.text
                loc = re.sub(r'<\?xml-stylesheet.*?\?>', '', loc)  # suppression instruction stylesheet qui peuvent bloquer le fonctionnement du sitemap

                # Filtrage des urls selon les exclusions
                if is_excluded(loc, exclusions):
                    continue

                # Appel récursif sur le sitemap enfant
                child_urls = extract_urls_sitemap(loc, base_url, exclusions, limit_date)
                urls.extend(child_urls)

        # Sitemap standard : liste d'urls
        elif soup.find('urlset'):
            for url in soup.find_all('url'):
                loc = url.loc.text
                
                # Filtrage des urls selon les exclusions
                if is_excluded(loc, exclusions):
                    continue
                
                # Si une date limite est définie (date du dernier scraping), on ne garde que les pages modifiées après cette date
                lastmod = url.find('lastmod')
                derniere_modif = None
                if lastmod:
                    try:
                        derniere_modif = datetime.fromisoformat(lastmod.text.replace("Z", "+00:00"))
                    except Exception:
                        pass
                    if limit_date and derniere_modif and derniere_modif < limit_date:
                        continue
                urls.append((loc, derniere_modif))

    except Exception as e:
        print(f"[ERREUR] Impossible de lire le sitemap : {sitemap_url} ({e})")
        return []

    # Affichage des sitemaps et urls extraites pour voir leur contenu
    #print(f"[DEBUG] URLs extraites du sitemap {sitemap_url} : {urls}")

    # Si aucune URL n'a été extraite, on retourne une liste vide
    if not urls:
        return urls

    # Correction des préfixes URL incohérents si nécessaire (sorbonne-universite qui devient upmc)
    urls = correct_url_prefix(urls, base_url.rstrip('/'))

    return urls

# ------------------------------------------------
# Calcule le nombre de pages qui ont été modifiées
# ------------------------------------------------

def count_modified_pages(config):

    sitemap_url = config.get("SITEMAP_URL", [])
    base_url = config.get("BASE_URL", "")
    exclusions = config.get("EXCLUDE_URL_KEYWORDS", [])

    # Date de dernière modification du site
    last_modified_date = config.get("LAST_MODIFIED_DATE", None)
    try:
        limit_date = datetime.strptime(last_modified_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        limit_date = None

    urls = extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date)
    return len(urls)
# -----------------------
# Imports des utilitaires
# -----------------------

import re
import requests
import time
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


def count_modified_pages_bis(config):

    start_time = time.time()

    sitemap_url = config.get("SITEMAP_URL", [])
    base_url = config.get("BASE_URL", "")
    exclusions = config.get("EXCLUDE_URL_KEYWORDS", [])

    # Date de dernière modification du site
    last_modified_date = config.get("LAST_MODIFIED_DATE", None)
    try:
        limit_date = datetime.strptime(last_modified_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        limit_date = None

    try:
        urls = extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date)
    except:
        urls = crawl_site(base_url, exclusions)

    res = len(urls)
    end_time = time.time()
    duration = end_time - start_time
    print(f"duration = {duration}")
    return res


# ------------------------------------------------
# Calcule le nombre de pages qui ont été modifiées
# ------------------------------------------------

def count_modified_pages(config):
    start_time = time.time()


    sitemap_url = config.get("SITEMAP_URL", [])
    base_url = config.get("BASE_URL", "")
    exclusions = config.get("EXCLUDE_URL_KEYWORDS", [])
    last_modified_date = config.get("LAST_MODIFIED_DATE", None)

    try:
        limit_date = datetime.strptime(last_modified_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        limit_date = None

    res =  extract_modified_urls_count(sitemap_url, base_url, exclusions, limit_date)
    end_time = time.time()
    duration = end_time - start_time
    print(f"duration = {duration}")
    return res

def extract_modified_urls_count(sitemap_url, base_url, exclusions, limit_date):

    count = 0

    try: 
        response = requests.get(sitemap_url, timeout=10, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.content.decode('utf-8', errors='ignore'), 'xml')

        # Cas d’un sitemap index (contenant d’autres sitemaps)
        if soup.find('sitemapindex'):
            for sitemap in soup.find_all('sitemap'):
                loc = sitemap.loc.text.strip()
                if is_excluded(loc, exclusions):
                    continue

                count += extract_modified_urls_count(
                    sitemap_url=loc,
                    base_url=base_url,
                    exclusions=exclusions,
                    limit_date=limit_date,
                )

        # Cas d’un sitemap normal
        elif soup.find('urlset'):
            for url_tag in soup.find_all('url'):
                loc = url_tag.loc.text.strip()

                if is_excluded(loc, exclusions):
                    continue

                lastmod = url_tag.find('lastmod')
                if lastmod and limit_date:
                    try:
                        date_modif = datetime.fromisoformat(lastmod.text.replace("Z", "+00:00"))
                        if date_modif < limit_date:
                            continue
                    except Exception:
                        continue

                count += 1

    except Exception as e:
        print(f"[ERREUR] Impossible de lire le sitemap {sitemap_url} ({e})")

    return count


######################################################################
#                            SANS SITEMAP                            #
######################################################################


# --------------------------------------
# Filtrage des extensions non HTML (PDF, DOC, PPT, etc.)
# --------------------------------------

def has_valid_extension(url):
    excluded_extensions = [
        '.pdf', '.doc', '.docx', '.ppt', '.pptx',
        '.xls', '.xlsx', '.zip', '.rar', '.jpg',
        '.jpeg', '.png', '.gif', '.mp4', '.mov',
        '.avi', '.mp3', '.csv'
    ]
    return not any(url.lower().endswith(ext) for ext in excluded_extensions)



# ------------------------------------------------
# Extraction d'URLs à partir de la page d'accueil
# ------------------------------------------------

def crawl_site(base_url, exclusions, max_urls=100):

    visited = set()
    urls_to_visit = [base_url]
    collected_urls = []

    try:
        while urls_to_visit and len(collected_urls) < max_urls:
            current_url = urls_to_visit.pop(0)

            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                response = requests.get(current_url, timeout=10, headers=HEADERS)
                response.raise_for_status()
            except Exception as e:
                print(f"[ERREUR] Échec de la requête vers {current_url} ({e})")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Normaliser l'URL
                if href.startswith('/'):
                    full_url = base_url.rstrip('/') + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue  # on ignore les ancres, javascript:, mailto:

                # Filtrage
                if is_excluded(full_url, exclusions) or not has_valid_extension(full_url):
                    continue

                # Filtrage par domaine et duplication
                if full_url.startswith(base_url) and full_url not in visited and full_url not in urls_to_visit:
                    try:
                        # Vérification : est-ce que l'URL retourne 200 ?
                        res = requests.head(full_url, headers=HEADERS, timeout=5, allow_redirects=True)
                        if res.status_code == 200:
                            collected_urls.append((full_url, None))
                            urls_to_visit.append(full_url)
                        else:
                            print(f"[INFO] Ignorée : {full_url} (status {res.status_code})")
                    except Exception as e:
                        print(f"[ERREUR] HEAD request échouée pour {full_url} ({e})")

                if len(collected_urls) >= max_urls:
                    break

    except Exception as e:
        print(f"[ERREUR] Impossible d'extraire les URLs depuis la page HTML ({e})")

    for url in collected_urls:
        print(url)

    return collected_urls

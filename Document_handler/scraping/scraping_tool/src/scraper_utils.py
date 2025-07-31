# -----------------------
# Imports des utilitaires
# -----------------------

import os
import requests
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Répertoire des fichiers de progression
PROGRESS_DIR = Path(__file__).resolve().parent.parent / "progress"
PROGRESS_DIR.mkdir(exist_ok=True)

# ---------------------------------
# User-agent pour les requêtes HTTP
# ---------------------------------
HEADERS = {
    "User-Agent": "PolytechScraper/0.8 (+https://github.com/Adr44mo/Stage-Chatbot-Polytech)"
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
        content = response.content.decode('utf-8', errors='ignore')

        # Trouver la première déclaration XML valide
        xml_start = content.find('<?xml')
        if xml_start > 0:
            content = content[xml_start:]

        # Parsing du contenu XML avec BeautifulSoup
        soup = BeautifulSoup(content, 'xml')

        # Sitemap index : liste de sitemaps
        if soup.find('sitemapindex'):
            sitemap_locs = [
                sitemap.loc.text.strip()
                for sitemap in soup.find_all('sitemap')
                if not is_excluded(sitemap.loc.text, exclusions)
            ]

            # Parallélisation
            cpu_cores = os.cpu_count() or 2
            max_workers = min(cpu_cores - 1, len(sitemap_locs))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(extract_urls_sitemap, loc, base_url, exclusions, limit_date): loc
                    for loc in sitemap_locs
                }
                for future in as_completed(futures):
                    try:
                        urls.extend(future.result())
                    except Exception as e:
                        print(f"[ERREUR] Extraction échouée pour {futures[future]} : {e}")

        # Sitemap standard : liste d'urls
        elif soup.find('urlset'):
            for url in soup.find_all('url'):
                loc = url.loc.text.strip()

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
        #cp.print_warning(f"Impossible de lire le sitemap : {sitemap_url} ({e})")
        raise e

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
        limit_date = datetime.fromisoformat(last_modified_date)
        if limit_date.tzinfo is None:
            limit_date = limit_date.replace(tzinfo=timezone.utc)
    except Exception:
        limit_date = None

    try:
        urls = extract_urls_sitemap(sitemap_url, base_url, exclusions, limit_date)
        return len(urls)
    
    # Valeur spéciale pour indiquer que le sitemap n'est pas accessible
    except Exception as e:
        #cp.print_warning(f"{config.get('NAME')} — Sitemap inaccessible : {e}")
        return -1


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

def crawl_site(base_url, exclusions, max_urls, verify_links=False, verbose=False):

    visited = set()
    urls_to_visit = [base_url]
    collected_urls = []
    all_found_urls = set()  # Pour éviter les doublons dans urls_to_visit
    failed_urls = set()  # Cache des URLs qui ont échoué pour éviter de les retester
    
    # Extraire le domaine de base pour filtrer les URLs malformées
    from urllib.parse import urlparse
    parsed_base = urlparse(base_url)
    domain_base = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    # Pre-compiler les patterns d'exclusion pour plus d'efficacité
    import re
    exclusion_patterns = [re.compile(re.escape(excl)) for excl in exclusions]
    
    if verbose:
        print(f"[INFO] Début du crawling de {base_url} (max {max_urls} URLs)")
        print(f"[INFO] Vérification des liens: {'Activée' if verify_links else 'Désactivée'}")

    try:
        while urls_to_visit and len(collected_urls) < max_urls:
            current_url = urls_to_visit.pop(0)

            if current_url in visited:
                continue

            if verbose:
                print(f"[INFO] Exploration de: {current_url} ({len(collected_urls)}/{max_urls} URLs collectées)")
            visited.add(current_url)

            try:
                # Optimisation : timeout plus court et pas de retry
                response = requests.get(current_url, timeout=5, headers=HEADERS)
                response.raise_for_status()
            except Exception as e:
                if verbose:
                    print(f"[ERREUR] Échec de la requête vers {current_url} ({e})")
                continue

            # Ajouter l'URL actuelle aux résultats
            collected_urls.append((current_url, None))

            # Optimisation : parsing HTML plus efficace
            soup = BeautifulSoup(response.text, 'html.parser')
            links_found_on_page = 0

            # Récupérer tous les liens d'un coup
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href'].strip()
                
                # Ignorer les liens vides
                if not href:
                    continue
                
                # Filtrage rapide des URLs malformées
                if ('.' in href and not href.startswith(('/', 'http', '#', 'mailto:', 'tel:', 'javascript:')) and '/' not in href[:10]):
                    continue
                
                # Normaliser l'URL
                if href.startswith('/'):
                    full_url = domain_base + href
                elif href.startswith('http'):
                    # Vérifier que c'est bien le même domaine
                    if not href.startswith(domain_base):
                        continue
                    full_url = href
                elif href.startswith('#'):
                    continue  # Ignorer les ancres
                elif href.startswith(('mailto:', 'tel:', 'javascript:')):
                    continue  # Ignorer les liens non-web
                else:
                    # URLs relatives sans slash initial
                    if '/' in current_url[len(domain_base):]:
                        # On est dans un sous-répertoire
                        current_path = '/'.join(current_url.split('/')[:-1])
                        full_url = current_path + '/' + href
                    else:
                        full_url = domain_base + '/' + href

                # Nettoyer l'URL
                if '#' in full_url:
                    full_url = full_url.split('#')[0]
                
                if '?' in full_url and not any(param in full_url for param in ['page=', 'id=', 'search=']):
                    full_url = full_url.split('?')[0]

                # Filtrage rapide par exclusions (pre-compiled regex)
                excluded = False
                for pattern in exclusion_patterns:
                    if pattern.search(full_url):
                        excluded = True
                        break
                
                if excluded or not has_valid_extension(full_url):
                    continue
                    
                # Éviter les doublons et les URLs qui ont déjà échoué
                if full_url in all_found_urls or full_url in failed_urls:
                    continue
                    
                all_found_urls.add(full_url)

                # Ajouter l'URL à la liste de visite
                if full_url not in visited:
                    if verify_links:
                        try:
                            res = requests.head(full_url, headers=HEADERS, timeout=2, allow_redirects=True)
                            if res.status_code == 200:
                                urls_to_visit.append(full_url)
                                links_found_on_page += 1
                            else:
                                failed_urls.add(full_url)
                        except Exception:
                            failed_urls.add(full_url)
                    else:
                        # Mode rapide : ajouter sans vérifier
                        urls_to_visit.append(full_url)
                        links_found_on_page += 1

                # Arrêter si on a atteint la limite
                if len(collected_urls) >= max_urls:
                    break
            
            if verbose and links_found_on_page > 0:
                print(f"[INFO] {links_found_on_page} nouveaux liens trouvés sur cette page")

    except Exception as e:
        print(f"[ERREUR] Erreur générale lors du crawling: {e}")

    if verbose:
        print(f"\n[RÉSULTAT] Crawling terminé: {len(collected_urls)} URLs collectées")
        if verify_links:
            print(f"[INFO] {len(failed_urls)} URLs ignorées pour erreurs HTTP")
        print("=" * 60)
        
        # Afficher toutes les URLs trouvées
        for i, (url, _) in enumerate(collected_urls, 1):
            print(f"{i:3d}. {url}")
    else:
        print(f"[RÉSULTAT] {len(collected_urls)} URLs collectées")

    return collected_urls


def crawl_site_fast(base_url, exclusions=None, max_urls=500):

    if exclusions is None:
        exclusions = []
        
    print(f"🚀 Crawling rapide de {base_url} (max {max_urls} URLs)")
    start_time = time.time()
    
    # Utiliser la fonction optimisée en mode rapide et silencieux
    urls = crawl_site(base_url, exclusions, max_urls, verify_links=False, verbose=False)
    
    elapsed = time.time() - start_time
    print(f"✅ Terminé en {elapsed:.2f}s - {len(urls)} URLs trouvées ({len(urls)/elapsed:.1f} URLs/sec)")
    
    return urls


def save_progress(site_name: str, current: int, total: int, status: str):
    """Sauvegarde l'état d'avancement du scraping dans un fichier JSON"""
    progress_path = PROGRESS_DIR / f"{site_name}.json"
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump({"site": site_name, "current": current, "total": total, "status": status}, f)

def clear_progress(site_name: str, status: str):
    """Supprime le fichier de progression une fois le scraping terminé"""
    progress_path = PROGRESS_DIR / f"{site_name}.json"
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump({"site": site_name, "current": 0, "total": 1, "status": status}, f)

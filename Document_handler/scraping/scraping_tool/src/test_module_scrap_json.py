import asyncio
import aiohttp
import random
import time
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
import hashlib
from datetime import datetime, timezone

from .scraper_utils import extract_urls_sitemap

HEADERS_BASE = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

MAX_CONCURRENT = 5

def hash_json(obj):
    filtered = {k: v for k, v in obj.items() if k not in ["lastmodif", "hash", "scraped_at"]}
    return hashlib.sha256(json.dumps(filtered, sort_keys=True).encode('utf-8')).hexdigest()

def normalize_filename(title, url, download_dir):
    import re
    import unicodedata
    from urllib.parse import urlparse

    title = title.replace('\u00A0', ' ').strip()
    title_norm = title.replace("œ", "oe").replace("Œ", "OE")
    nfkd_form = unicodedata.normalize('NFKD', title_norm)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8').lower()
    title_norm = re.sub(r'\W+', '_', only_ascii).strip('_')

    base_filename = f"{title_norm}.json"
    base_path = download_dir / base_filename

    if base_path.exists():
        try:
            with open(base_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("url") == url:
                return base_filename
            else:
                parsed = urlparse(url)
                path_suffix = parsed.path.strip("/").replace("/", "_")
                fallback_filename = f"{title_norm}_{path_suffix}.json"
                return fallback_filename
        except Exception:
            parsed = urlparse(url)
            path_suffix = parsed.path.strip("/").replace("/", "_")
            return f"{title_norm}_{path_suffix}.json"
    return base_filename

def extract_title(soup, url):
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True).replace('\u00A0', ' ')
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True).replace('\u00A0', ' ')
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split('/') if part]
    return parts[-1] if parts else "no_title"

def extract_main_content(soup):
    # Simplification pour l’exemple (tu peux reprendre ta fonction plus complète)
    text = soup.get_text(separator="\n", strip=True)
    return text

async def fetch(session, url, semaphore):
    headers = {
        "User-Agent": random.choice(HEADERS_BASE)
    }
    async with semaphore:
        try:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 429:
                    print(f"[WARN] 429 Too Many Requests for {url}, waiting 30s...")
                    await asyncio.sleep(30)
                    return await fetch(session, url, semaphore)  # retry after wait
                resp.raise_for_status()
                return await resp.text()
        except Exception as e:
            print(f"[ERROR] Requête échouée pour {url} : {e}")
            return None

async def scrape_page(session, url, download_dir, existing_by_url):
    html = await fetch(session, url, semaphore)
    if html is None:
        return 0

    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup, url)
    content = extract_main_content(soup)
    if not content:
        print(f"[WARN] Contenu vide pour {url}")
        return 0

    now_date = datetime.now(timezone.utc).isoformat()
    parsed = urlparse(url)
    site = parsed.netloc.replace("www.", "")
    parts = [p for p in parsed.path.split('/') if p]
    category = parts[1] if len(parts) >= 2 else (parts[0] if parts else "NA")

    json_obj = {
        "url": url,
        "site": site,
        "category": category,
        "title": title,
        "hash": "NA",
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
            print(f"[INFO] Fichier identique déjà présent : {filepath.name}")
            return 0
        else:
            print(f"[INFO] Mise à jour du fichier existant : {filepath.name}")
    else:
        filename = normalize_filename(title, url, download_dir)
        filepath = download_dir / filename

    json_obj["hash"] = hash_json(json_obj)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=4)
        print(f"[DOWNLOAD] {filepath.name}")
        return 1
    except Exception as e:
        print(f"[ERROR] Écriture échouée de {filepath} : {e}")
        return 0

async def main_crawl(site_config):
    global semaphore
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    base_url = site_config["BASE_URL"]
    sitemap_url = site_config["SITEMAP_URL"]
    download_dir = Path(site_config["JSON_DOWNLOAD_DIR"])
    exclusions = site_config.get("EXCLUDE_URL_KEYWORDS", [])

    download_dir.mkdir(parents=True, exist_ok=True)

    # Supposons que tu as une fonction extract_urls_sitemap() synchrone déjà définie
    urls_and_dates = extract_urls_sitemap(sitemap_url, base_url, exclusions, None)
    urls_pages = [u for u, _ in urls_and_dates]

    existing_by_url = {}
    for filepath in download_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                url_ = data.get("url")
                if url_:
                    existing_by_url[url_] = {"filepath": filepath, "data": data}
        except Exception:
            pass

    async with aiohttp.ClientSession() as session:
        tasks = []
        total_new = 0
        for url in urls_pages:
            task = asyncio.create_task(scrape_page(session, url, download_dir, existing_by_url))
            tasks.append(task)
            # Petite pause aléatoire pour étaler les requêtes
            await asyncio.sleep(random.uniform(0.1, 0.3))

        results = await asyncio.gather(*tasks)
        total_new = sum(results)
        print(f"\n🔗 {len(urls_pages)} pages traitées, {total_new} nouvelles/actualisées.")

if __name__ == "__main__":
    import sys
    site_config = {
        "BASE_URL": "https://tonsite.ecole.fr",
        "SITEMAP_URL": "https://tonsite.ecole.fr/sitemap.xml",
        "JSON_DOWNLOAD_DIR": "./json_data",
        "EXCLUDE_URL_KEYWORDS": [],
    }
    asyncio.run(main_crawl(site_config))

# Pour lancer le crawl (exemple) :
if __name__ == "__main__":
    site_config = {
        "BASE_URL": "https://www.polytech.sorbonne-universite.fr/",
        "SITEMAP_URL": "https://www.polytech.sorbonne-universite.fr/sitemap.xml",
        "JSON_DOWNLOAD_DIR": "Document_handler/scraping/scraping_tool/src/data_json",
        "EXCLUDE_URL_KEYWORDS": ["/actualites"],
        "LAST_MODIFIED_DATE": None,  # ou "2023-01-01"
    }
    start = time.time()
    asyncio.run(main_crawl(site_config))
    end = time.time()
    print(f"duration = {end-start}")

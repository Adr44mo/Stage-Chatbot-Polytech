import os
from pathlib import Path
import shutil
from urllib.parse import urlparse

# Fichier template pour la configuration du site
TEMPLATE_PATH = Path(__file__).parent / 'config_template.yaml'

# Dossier de sortie par défaut pour les fichiers yaml
CONFIG_DIR = Path(__file__).parent.parent / 'scraping_tool' / 'config_sites'
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Dossier d'archivage 
ARCHIVE_DIR = CONFIG_DIR / 'config_archives'
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Dossier des documents du site
DATA_DIR = Path(__file__).parent.parent.parent / 'Corpus' / 'data_sites'
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_ARCHIVE_DIR = DATA_DIR / 'archives'
DATA_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Dossier du log du site
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_ARCHIVE_DIR = LOG_DIR / 'archives'
LOG_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------
# Fonction pour générer la configuration du site
# ----------------------------------------------

def generate_config(site_name, url):

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    # Normalisation de l'url de base
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Url du sitemap
    sitemap_url = f"{base_url}/sitemap.xml"

    # Création de la configuration du site
    rendered = template.format(
        NAME=site_name,
        BASE_URL=base_url,
        SITEMAP_URL=sitemap_url
    )

    # Écriture de la configuration dans un fichier YAML
    filename = f"{site_name.replace(' ', '_').lower()}.yaml"
    config_path = os.path.join(CONFIG_DIR, filename)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(rendered)

    print(f"[INFO] Fichier de configuration généré : {config_path}")

# -------------------------------------------------
# Fonction pour archiver la configuration d'un site
# -------------------------------------------------

def archive_config(site_name):

    # Fichier de config
    filename = f"{site_name.strip().replace(' ', '_').lower()}.yaml"
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        return
    arch_path = ARCHIVE_DIR / filename

    # Documents du site
    data_name = filename.replace('.yaml', '')
    data_path = DATA_DIR / data_name
    if data_path.exists():
        data_arch_path = DATA_ARCHIVE_DIR / data_name

    # Log du site
    log_name = filename.replace('.yaml', '.txt')
    log_path = LOG_DIR / log_name
    if log_path.exists():
        log_arch_path = LOG_ARCHIVE_DIR / log_name

    shutil.move(config_path, arch_path)
    print(f"[INFO] Fichier de configuration archivé : {config_path}")
    if data_arch_path.exists():
        shutil.move(data_path, data_arch_path)
        print(f"[INFO] Fichier de configuration archivé : {data_path}")
    if log_arch_path.exists():
        shutil.move(log_path, log_arch_path)
        print(f"[INFO] Fichier de configuration archivé : {log_path}")


# -------------------------------------------
# Fonction principale pour exécuter le script
# -------------------------------------------

def main():

    print("Entrez 1 pour la génération ; 0 pour l'archivage :")
    choice = int(input().strip())

    print("Entrez le nom du site :")
    site_name = input().strip()

    if choice == 1:
        print("Entrez l'URL du site :")
        url = input().strip()

        generate_config(site_name, url)
    
    else:
        archive_config(site_name)


if __name__ == "__main__":
    main()

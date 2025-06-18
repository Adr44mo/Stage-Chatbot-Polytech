import os
import yaml
from urllib.parse import urlparse

# Fichier template pour la configuration du site
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'config_template.yaml')

# Dossier de sortie par défaut pour les fichiers yaml
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'scraping_tool', 'config_sites')
os.makedirs(CONFIG_DIR, exist_ok=True)

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
        SITEMAP_URL=sitemap_url,
        EXCLUDE_URL_KEYWORDS="/actualites/"
    )

    # Écriture de la configuration dans un fichier YAML
    filename = f"{site_name.replace(' ', '_').lower()}.yaml"
    config_path = os.path.join(CONFIG_DIR, filename)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(rendered)

    print(f"[INFO] Fichier de configuration généré : {config_path}")

# -------------------------------------------
# Fonction principale pour exécuter le script
# -------------------------------------------

def main():

    print("Entrez le nom du site :")
    site_name = input().strip()

    print("Entrez l'URL du site :")
    url = input().strip()

    generate_config(site_name, url)

if __name__ == "__main__":
    main()

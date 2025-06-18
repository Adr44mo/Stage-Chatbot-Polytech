# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import time
import os
from datetime import datetime
from ruamel.yaml import YAML

# Imports des modules de scrap
import src.module_scrap_pdf
import src.module_scrap_json
from src.scraper_utils import count_modified_pages

# Initialisation de l'instance YAML & configuration des options de mise en forme
ruamel_yaml = YAML()
ruamel_yaml.preserve_quotes = True
ruamel_yaml.indent(mapping=2, sequence=4, offset=2)

# -------------------------
# Ouverture de fichier yaml
# -------------------------

def load_yaml(path):

    with open(path, "r", encoding="utf-8") as f:
        return ruamel_yaml.load(f)

# -------------------------------------------------------------------------------------
# Mise à jour de la date de dernière modification dans le fichier de configuration yaml
# -------------------------------------------------------------------------------------

def update_date_config(config_path):

    try:

        # Lecture du fichier YAML original
        config_data = load_yaml(config_path)

        # Mise à jour de la date
        config_data["LAST_MODIFIED_DATE"] = datetime.now().strftime("%Y-%m-%d")

        # Réécriture du fichier YAML sans perte de style
        with open(config_path, 'w', encoding='utf-8') as f:
            ruamel_yaml.dump(config_data, f)

        print(f"[INFO] Date de dernier scraping mise à jour dans le fichier {os.path.basename(config_path)}\n")
    
    except Exception as e:
        print(f"[ERREUR] Impossible de mettre à jour {config_path} : {e}")

# -------------------------------------------------
# Affichage du menu pour le choix du site à scraper
# -------------------------------------------------

def menu(config_files, config_dir):

    # Affichage du menu 
    print("Sélectionnez le site à scraper : \n")
    print("0. Tous les sites")
    for i, file in enumerate(config_files, start=1):
        config_path = os.path.join(config_dir, file)
        site_name = file.replace(".yaml", "").replace("_", " ").title()
        try:
            config = load_yaml(config_path)
            update_count = count_modified_pages(config)
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur lors du traitement de {file} : {e}")
            update_count = "?"

        print(f"{i}. {site_name} (pages modifiées : {update_count})")

    # Saisie de l'utilisateur
    while True:
        try:
            choice = int(input("\nEntrez un numéro du site : "))
            if 0 <= choice <= len(config_files):
                return choice
            else:
                print("Veuillez entrer un numéro valide.")
        
        except ValueError:
            print("Entrée invalide, veuillez entrer un numéro.")

# ------------------
# Scraping d'un site
# ------------------

def scrap(site, config_path, base_dir, log_dir):

    # Création du dossier de données pour le site
    site_name = site["NAME"]
    base_data_dir = os.path.abspath(os.path.join(base_dir, "..", "data_sites", site_name.replace(" ", "_").lower()))
    os.makedirs(base_data_dir, exist_ok=True)

    # Ajouter dynamiquement les chemins de travail dans la config (en mémoire seulement)
    site["DATA_DIR"] = base_data_dir
    site["PDF_DOWNLOAD_DIR"] = os.path.join(base_data_dir, "pdf_scrapes")
    site["JSON_DOWNLOAD_DIR"] = os.path.join(base_data_dir, "json_scrapes")
    os.makedirs(site["PDF_DOWNLOAD_DIR"], exist_ok=True)
    os.makedirs(site["JSON_DOWNLOAD_DIR"], exist_ok=True)

    print(f"\n\n============== Scraping du site : {site_name} ==============\n")

    log_filename = f"{os.path.basename(config_path).replace(".yaml", "")}.txt"
    log_path = os.path.join(log_dir, log_filename)

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("==========================================================\n")
        log_file.write(f"\n             Scraping du site : {site_name}             \n")
        log_file.write(f"\nLe dernier scraping en date a été effectué le {datetime.now().strftime("%d/%m/%Y à %H:%M")}\n\n")

        # Scraping des PDF
        print("\n⌛ Étape 1/2 : Lancement du scraping des PDF\n")
        time.sleep(1)
        src.module_scrap_pdf.scrape_page(site)
        pdf_pages = len(src.module_scrap_pdf.visited_pages)
        pdf_count = src.module_scrap_pdf.new_download_count
        print("\n✅ Scraping des PDF terminé ! \n")
        print(f"Nombre de pages web visitées : {pdf_pages}")
        print(f"Nombre de PDF téléchargés ou mis à jour : {pdf_count}")
        log_file.write(f"  - Pages visitées (PDF)  : {pdf_pages}\n")
        log_file.write(f"  - PDF téléchargés       : {pdf_count}\n\n")
        time.sleep(1)

        # Scraping des JSON
        print("\n⌛ Étape 2/2 : Lancement du scraping des JSON\n")
        time.sleep(1)
        src.module_scrap_json.crawl(site)
        json_pages = len(src.module_scrap_json.visited_pages)
        json_count = src.module_scrap_json.new_json_count
        print("\n✅ Scraping des JSON terminé ! \n")
        print(f"Nombre de pages web visitées : {json_pages}")
        print(f"Nombre de JSON téléchargés ou mis à jour : {json_count}\n")
        log_file.write(f"  - Pages visitées (JSON) : {json_pages}\n")
        log_file.write(f"  - JSON téléchargés      : {json_count}\n\n")
        time.sleep(1)

        log_file.write("\n✅ Scraping terminé pour ce site.\n")
        log_file.write("\n\nAttention : parfois, les fichiers téléchargés/mis à jour le sont par précaution et non pas parce qu'ils sont nouveaux. \n\n")
        log_file.write("==========================================================\n")


    # Enregistrement du log dans le dossier parent
    print("\n✅ log_scraping.txt enregistré avec succès dans le dossier parent ! \n")

    # Mise à jour de la date de dernière modification dans le fichier YAML
    update_date_config(config_path)

    print("\n============== SCRAPING DU SITE WEB TERMINÉ ==============\n")


#-------------------------------------------------------------------
# Définition de la fonction principale main() : on effectue le scrap
# en appelant les modules et on enregistre ensuite un log en .txt
#-------------------------------------------------------------------

def main():

    print("\n============== SCRIPT DE SCRAPING DE SITE WEB ==============\n")

    # Dossier des configs et des logs
    base_dir = os.path.dirname(__file__)
    config_dir = os.path.join(base_dir, "config_sites")
    log_dir = os.path.abspath(os.path.join(base_dir, "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)

    # Fichier de configuration du scraping
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.yaml')]
    if not config_files:
        print("[ERREUR] Aucun fichier de configuration trouvé dans le dossier 'config_sites'.")
        return
    
    # Affichage du menu et détermination des fichiers de configuration à utiliser
    choice = menu(config_files, config_dir)
    selected_configs = config_files if choice == 0 else [config_files[choice - 1]]
    
    # Chargement de la configuration du scraping pour chaque site
    for config_file in selected_configs:

        # Chargement et récupération des paramètres de scrap depuis le .YAML
        config_path = os.path.join(config_dir, config_file)
        site = load_yaml(config_path)
        scrap(site, config_path, base_dir, log_dir)      

# -----------------------------------------------------------------------------
# Fonction principale de type 'if __name__ == "__main__":'
# ATTENTION : CETTE FONCTION N'EST PAS EXECUTEE AUTOMATIQUEMENT EN CAS D'IMPORT
# Cela ne pose pas de problème puisque ce scraping_script.py n'est pas importé
# dans d'autres fichiers. Il doit être éxécuté seul pour régénérer le corpus
# si besoin (si le site a évolué, s'il contient de nouveaux pdf, etc...)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()

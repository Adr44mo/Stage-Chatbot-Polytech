import src.module_scrap_pdf
import src.module_scrap_json
import time
import os
from datetime import datetime

def main():

    print("\n============== SCRIPT DE SCRAPING DU SITE WEB ==============\n")

    # Scraping des PDF
    print("\n⌛ Étape 1/2 : Lancement du scraping des PDF\n")
    time.sleep(3)
    src.module_scrap_pdf.scrape_page(src.module_scrap_pdf.BASE_URL)
    print("\n✅ Scraping des PDF terminé ! \n")
    print(f"Nombre de pages web visitées : {len(src.module_scrap_pdf.visited_pages)}")
    print(f"Nombre de PDF téléchargés ou mis à jour : {src.module_scrap_pdf.new_download_count}")
    time.sleep(3)
    
    # Scraping des JSON
    print("\n⌛ Étape 2/2 : Lancement du scraping des JSON\n")
    time.sleep(7)
    src.module_scrap_json.crawl(src.module_scrap_json.BASE_URL)
    print("\n✅ Scraping des JSON terminé ! \n")
    print(f"Nombre de pages web visitées : {len(src.module_scrap_json.visited_urls)}")
    print(f"Nombre de JSON téléchargés ou mis à jour : {src.module_scrap_json.new_json_count}")

    #Enregistrement du Log.txt
    formatted_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    log_filename = "../log_scraping.txt"
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log_file.write("===================================================\n")
        log_file.write(f"\nLe dernier scraping en date a été effectué le {formatted_date}\n")
        log_file.write(f"\nNombre de PDF téléchargés ou mis à jour : {src.module_scrap_pdf.new_download_count}")
        log_file.write(f"\nNombre de JSON téléchargés ou mis à jour : {src.module_scrap_json.new_json_count}")
        log_file.write("\n\nAttention : parfois, les fichiers téléchargés/mis à jour le sont par précaution et non pas parce qu'ils sont nouveaux. \n")
        log_file.write("\n===================================================\n\n")
    print("\n✅ log_scraping.txt enregistré dans le dossier parent ! \n")

    print("\n============== SCRAPING DU SITE WEB TERMINÉ ==============\n")

if __name__ == "__main__":
    main()
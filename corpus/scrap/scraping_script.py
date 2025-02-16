import src.module_scrap_pdf  # Assurez-vous que scraper.py est dans le même répertoire ou dans le PYTHONPATH
import time

def main():

    print("\n============== SCRIPT DE SCRAPING DU SITE WEB ==============\n")

    # Scraping des PDF
    print("\n⌛ Étape 1/2 : Lancement du scraping des PDF\n")
    time.sleep(3)
    src.module_scrap_pdf.scrape_page(src.module_scrap_pdf.BASE_URL)
    print("\n✅ Scraping des PDF terminé ! \n")
    print(f"Pages web visitées : {len(src.module_scrap_pdf.visited_pages)}")
    print(f"Nouveaux PDF téléchargés : {src.module_scrap_pdf.new_download_count}")
    time.sleep(3)
    
    # Scraping des JSON
    print("\n⌛ Étape 2/2 : Lancement du scraping des JSON\n")
    time.sleep(7)
    print("\n✅ Scraping des JSON terminé ! \n")

    print("\n============== SCRAPING DU SITE WEB TERMINÉ ==============\n")

if __name__ == "__main__":
    main()
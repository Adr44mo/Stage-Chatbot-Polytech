import os
import sys
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
from readability import Document
import logging
from urllib.parse import urlunparse, urlparse

# GLOBAL VARIABLES
main_domain = "www.polytech.sorbonne-universite.fr"
output_directory = "scraped_data"
visited_urls = set()
allowed_external_domains = [
    "geipi-polytech.org"
    "sorbonne-universite.fr",
    "sciences.sorbonne-universite.fr"
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scrape.log", mode='w'),
        logging.StreamHandler()
    ]
)

def main():
    start_url = f"https://{main_domain}/"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    scrape_page(start_url, depth=0)

def scrape_page(url, depth):
    """
    Scrapes a single page, extracts content, saves it as JSON, and follows links recursively.
    """
    # Before scraping a page, check if its URL has already been visited*
    url = normalize_url(url)
    if url in visited_urls:
        return
    visited_urls.add(url)
    
    # Request the page and parse the HTML content using BeautifulSoup
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout) as e:
        logging.error(f"Failed to retrieve {url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract page information
    page_title = soup.title.string.strip() if soup.title and soup.title.string else url
    page_content = extract_text_content(response.text)

    # Determine basic metadata categories (category1, category2, etc.)
    categories = assign_basic_metadata_categories(url)

    # Create JSON data
    page_data = {
        "title": page_title,
        "url": url,
        "content": page_content,
        **categories  # Unpack category dictionary
    }

    # Save the JSON data to a file
    save_json(page_data, url)

    # Find and follow links within the page
    follow_links(soup, url, depth)

def extract_text_content(html):
    doc = Document(html)
    readable_html = doc.summary()
    readable_text = BeautifulSoup(readable_html, 'html.parser').get_text(separator=' ')
    return ' '.join(readable_text.split())

def normalize_url(url):
    parsed = urlparse(url)
    # Remove query and fragment by setting them to empty
    normalized = parsed._replace(query="", fragment="")
    # Remove trailing slash from path
    normalized_path = normalized.path.rstrip('/')
    normalized = normalized._replace(path=normalized_path)
    return urlunparse(normalized)

def assign_basic_metadata_categories(url):
    """
    Assigns BASIC metadata categories to a given URL.
    This currently splits the URL path by '/' to get an approximation of categories and uses the URL's domain for category1.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path_parts = [part for part in parsed_url.path.split('/') if part]

    categories = {
        "category1": domain
    }
    
    # Assigning path parts to categories
    for i, part in enumerate(path_parts, start=2):
        categories[f"category{i}"] = part or "NA"

    # TODO: Additional fields
    categories["filierespecifique"] = "NA"
    categories["datespecifique"] = "NA"

    return categories

def save_json(data, url):
    """
    Saves the scraped data as a JSON file. The file name is derived from the page URL.
    """
    # Sanitize the filename
    parsed_url = urlparse(url)
    filename = parsed_url.path.strip('/').replace('/', '_') or 'index'
    # If the filename is empty or just whitespace, set it to something valid
    if not filename.strip():
        filename = parsed_url.netloc
    filename = f"{filename}.json"
    file_path = os.path.join(output_directory, filename)

    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    logging.info(f"Saved: {file_path}")

def follow_links(soup, current_url, depth):
    """
    Finds links in the current page and follows them.
    """
    current_url = normalize_url(current_url)
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        # Construct full URL
        full_url = urljoin(current_url, href)
        parsed_full_url = urlparse(full_url)

        # Skip empty or invalid URLs
        if not parsed_full_url.scheme or not parsed_full_url.netloc:
            continue

        # TODO: Handle PDFs
        if is_pdf_url(full_url):
            continue

        if parsed_full_url.netloc == main_domain:
            # Internal link: follow without depth limit
            if full_url not in visited_urls:
                scrape_page(full_url, depth)
        elif parsed_full_url.netloc in allowed_external_domains:
            # External allowed domain: only follow if depth is less than 1
            if depth < 1 and full_url not in visited_urls:
                scrape_page(full_url, depth + 1)
        else:
            continue

def is_pdf_url(url):
    return url.lower().endswith('.pdf') or ('application/pdf' in url.lower())

if __name__ == "__main__":
    main()
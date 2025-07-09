import json
from pathlib import Path

def normalize_entry(raw_entry: dict, chemin_local: str, site_name: str) -> dict:
    return {
        "document_type": "page_web",
        "metadata": {
            "title": raw_entry.get("title", "Sans titre")
        },
        "source": {
            "category": "scrapping",
            "chemin_local": chemin_local,
            "url": raw_entry.get("url"),
            "site": raw_entry.get("site", site_name)
        },
        "content": raw_entry.get("content", ""),
        "tags": [],
        "type_specific": {}
    }


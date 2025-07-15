import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OLLAMA_MODEL = "mistral"
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-3.5-turbo"

BASE_DIR = Path(__file__).parent
CORPUS_DIR = BASE_DIR.parent / "Corpus"
DATA_SITES_DIR = CORPUS_DIR / "data_sites"
PDF_MAN_DIR = CORPUS_DIR / "pdf_man"

PREPROCESSING_DIR = BASE_DIR / "preprocessing"
INPUT_MAPS = PREPROCESSING_DIR / "input_maps"
OUTPUT_MAPS = PREPROCESSING_DIR / "output_maps"
VECT_MAPS = PREPROCESSING_DIR / "vect_maps"
INPUT_MAPS.mkdir(parents=True, exist_ok=True)
OUTPUT_MAPS.mkdir(parents=True, exist_ok=True)
VECT_MAPS.mkdir(parents=True, exist_ok=True)

INPUT_DIR = CORPUS_DIR / "test"
VALID_DIR = CORPUS_DIR / "json_normalized" / "validated"
REJECTED_DIR = CORPUS_DIR / "json_normalized" / "rejected"
PROCESSED_DIR = CORPUS_DIR / "json_normalized" / "processed"
PROMPTS_DIR = BASE_DIR / "prompts"

VALID_DIR.mkdir(parents=True, exist_ok=True)
REJECTED_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA_PATH = BASE_DIR / "schema" / "polytech_schema.json"
with open(SCHEMA_PATH, encoding="utf-8") as f:
    SCHEMA = json.load(f)

TEST_DIR = BASE_DIR.parents[1] / "Test" / "Color"
sys.path.append(str(TEST_DIR))


from colored_print import ColorPrint

ColorPrint.print_info("Configuration chargée avec succès.")
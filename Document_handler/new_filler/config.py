import os
from pathlib import Path
import json

from dotenv import load_dotenv
import sys

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OLLAMA_MODEL = "mistral"
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-3.5-turbo"

BASE_DIR = Path(__file__).parent
CORPUS_DIR = BASE_DIR.parent / "Corpus"
#INPUT_DIR = CORPUS_DIR / "json_Output_pdf&Scrap"
INPUT_DIR = CORPUS_DIR / "test"
VALID_DIR = CORPUS_DIR / "json_normalized" / "validated"
REJECTED_DIR = CORPUS_DIR / "json_normalized" / "rejected"
PROMPTS_DIR = BASE_DIR / "prompts"

VALID_DIR.mkdir(parents=True, exist_ok=True)
REJECTED_DIR.mkdir(parents=True, exist_ok=True)
SCHEMA_PATH = BASE_DIR / "schema" / "polytech_schema.json"
with open(SCHEMA_PATH, encoding="utf-8") as f:
    SCHEMA = json.load(f)

INPUT_MAPS = Path(__file__).parent / "preprocessing" / "input_maps"
VECT_MAPS = Path(__file__).parent / "preprocessing" / "vect_maps"
OUTPUT_MAPS = Path(__file__).parent / "preprocessing" / "output_maps"

TEST_DIR = BASE_DIR.parents[1] / "Test" / "Color"

sys.path.append(str(TEST_DIR))

from colored_print import ColorPrint

ColorPrint.print_info("Configuration chargée avec succès.")
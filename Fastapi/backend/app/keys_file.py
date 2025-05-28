# --------------------------------------------------------------------
# SI ON SOUHAITE IMPORTER LES VALEURS PAR ENVIRONNEMENT, UTILISER CECI
# --------------------------------------------------------------------

import os
from dotenv import load_dotenv

# Trouve le fichier .env s'il existe puis le charge dans l'environnement
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_PATH):
    load_dotenv()

# Récupérer les variables d’environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_API_URL = os.getenv("HF_API_URL")
HF_API_URL_EMBEDDING = os.getenv("HF_API_URL_EMBEDDING")


# ----------------------------------------------------------------
# SI ON SOUHAITE IMPORTER LES VALEURS EXPLICITEMENT, UTILISER CECI
# ----------------------------------------------------------------

# OPENAI_API_KEY = ""

# HF_API_TOKEN = ""

# HF_API_URL = ""

# HF_API_URL_EMBEDDING = ""
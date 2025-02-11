# --------------------------------------------------------------------
# SI ON SOUHAITE IMPORTER LES VALEURS PAR ENVIRONNEMENT, UTILISER CECI
# --------------------------------------------------------------------

# from dotenv import dotenv_values
# venv = dotenv_values(".env")
# OPENAI_API_KEY = venv.get("OPENAI_API_KEY")
# HF_API_TOKEN = venv.get("HF_API_TOKEN")
# HF_API_URL = venv.get("HF_API_URL")

# ----------------------------------------------------------------
# SI ON SOUHAITE IMPORTER LES VALEURS EXPLICITEMENT, UTILISER CECI
# ----------------------------------------------------------------

# CLE OPENAI
# La cle ci-dessous est celle utilisee pour le developpement du RAG
# Elle est alimentee par le portefeuille de polytech sorbonne 

OPENAI_API_KEY = "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"

# TOKEN API HUGGINGFACE
# Le token ci-dessous fait actuellement des requetes au serveur huggingface de la maquette
# Elle est alimentee par le portefeuille de tristan chenaille 

HF_API_TOKEN = "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"

# URL SERVEUR HUGGINGFACE
# Cette URL correspond au serveur huggingface de la maquette

HF_API_URL = "https://aa5fwfof4d7tb5sy.us-east-1.aws.endpoints.huggingface.cloud"

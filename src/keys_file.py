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
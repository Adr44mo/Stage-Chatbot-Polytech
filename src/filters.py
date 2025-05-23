# -----------------------
# Imports des utilitaires
# -----------------------

# Imports de librairies
import torch
import re
import unicodedata

# Imports d'éléments spécifiques externes
from sentence_transformers import SentenceTransformer, util
from langdetect import detect

# ----------------------------------------------------------------------
# Détection d'intentions simples (salutations, remerciements, etc.) pour
# ignorer les messages "inutiles" et éviter des appels coûteux à l'API
# ----------------------------------------------------------------------

# Chargement du modèle multilingue pour alterner entre français/anglais
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2") 

# Dictionnaire d'intentions
INTENTS = {
    "fr": {
        "greeting": ["bonjour", "salut", "coucou", "bonsoir"],
        "thanks": ["merci", "merci beaucoup", "je vous remercie"],
        "goodbye": ["au revoir", "à bientôt", "à plus tard", "ciao"],
        "acknowledgment": ["d'accord", "bien reçu", "ok", "entendu"]
    },
    "en": {
        "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
        "thanks": ["thanks", "thank you", "thanks a lot", "appreciated"],
        "goodbye": ["bye", "goodbye", "see you", "see ya"],
        "acknowledgment": ["okay", "sure", "got it", "noted"]
    }
}

# Réponses automatiques
RESPONSES = {
    "fr": {
        "greeting": "Bonjour ! Posez-moi vos questions sur Polytech Sorbonne 😊",
        "thanks": "Avec plaisir !",
        "goodbye": "Au revoir ! À bientôt 👋",
        "acknowledgment": "Parfait !"
    },
    "en": {
        "greeting": "Hello! Ask me anything about Polytech Sorbonne 😊",
        "thanks": "You're welcome!",
        "goodbye": "Goodbye! See you soon 👋",
        "acknowledgment": "Great!"
    }
}

# ------------------
# Nettoyage du texte
# ------------------

def clean_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

# ----------------------------------------------------------------
# Génère et stocke les embeddings pour chaque exemple d'intention 
# ----------------------------------------------------------------

def build_intent_embeddings():
    intent_embeddings = {}
    for lang, intent_dict in INTENTS.items():
        intent_embeddings[lang] = {}
        for intent, examples in intent_dict.items():
            intent_embeddings[lang][intent] = model.encode(examples, convert_to_tensor=True)
    return intent_embeddings

# Embeddings de référence (générés une fois et stockés au chargement du module)
INTENT_EMBEDDINGS = build_intent_embeddings()

# --------------------------------
# Détection automatique de langue
# --------------------------------

def detect_language(text):
    try:
        lang = detect(text)
        return "en" if lang == "en" else "fr"
    except:
        return "fr"

# ----------------------------------------------------------------------------------------
# Classification d'une intention avec un seuil de similarité (+ vérification de la langue)
# ----------------------------------------------------------------------------------------

def classify_intent(text, detected_lang, threshold=0.80):
    cleaned = clean_text(text)
    input_emb = model.encode(cleaned, convert_to_tensor=True)

    best_intent = None
    best_lang = detected_lang
    best_score = 0

    for lang in ["fr", "en"]:
        intents = INTENT_EMBEDDINGS[lang]
        for intent, ref_embs in intents.items():
            score = util.cos_sim(input_emb, ref_embs).max().item()
            print(f"[Lang: {lang} | Intent: {intent}] Similarité: {score:.3f}") # DEBUG
            if score > best_score:
                best_score = score
                best_intent = intent
                best_lang = lang

    if best_score >= threshold:
        return best_lang, best_intent
    return detected_lang, None

# -------------------------------------------------------
# Réponse automatique en fonction de l'intention détectée
# -------------------------------------------------------

def handle_if_uninformative(text):
    detected_lang = detect_language(text)
    final_lang, intent = classify_intent(text, detected_lang)
    if intent:
        return RESPONSES[final_lang].get(intent)
    return None


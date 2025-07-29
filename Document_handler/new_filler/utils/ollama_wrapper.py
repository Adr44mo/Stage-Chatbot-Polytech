"""
Module d'interrogation de modèles de langage (LLM).

Ce module fournit une interface unifiée pour envoyer des prompts à des modèles
locaux (via Ollama) ou distants (via l'API OpenAI).

Fonctionnalités :
- Routage automatique du prompt vers le bon moteur (OpenAI ou Ollama)
- Gestion des erreurs et des timeouts
- Appels via subprocess ou API OpenAI

Exemples d'utilisation :
    response = ask_model("Explique la gravité en 2 phrases.", engine="openai")
    print(response)

Configuration requise :
- Définir les variables `OLLAMA_MODEL`, `OPENAI_MODEL`, et `OPENAI_API_KEY` dans le fichier config

"""
import subprocess
import openai
import os
from ..config import OLLAMA_MODEL, OPENAI_MODEL, OPENAI_API_KEY

def ask_model(prompt: str, engine: str = "openai") -> str:
    """
    Envoie un prompt au modèle spécifié (OpenAI ou Ollama).

    Args:
        prompt (str): Le prompt à envoyer au modèle.
        engine (str): Le moteur à utiliser, "openai" ou "ollama".

    Returns:
        str: La réponse générée par le modèle.

    Raises:
        ValueError: Si le moteur spécifié est inconnu.
    """
    if engine == "ollama":
        return ask_ollama(prompt)
    elif engine == "openai":
        return ask_openai(prompt)
    else:
        raise ValueError(f"❌ Unknown engine: {engine}")

def ask_ollama(prompt: str) -> str:
    """
    Interroge un modèle local via Ollama.

    Args:
        prompt (str): Le prompt à envoyer.

    Returns:
        str: La réponse du modèle Ollama.

    Raises:
        RuntimeError: Si Ollama échoue ou ne retourne rien.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=60
        )
        output = result.stdout.decode("utf-8").strip()
        if not output:
            raise RuntimeError("Ollama n’a rien retourné.")
        return output
    except subprocess.TimeoutExpired:
        raise RuntimeError("⏱️ Timeout pendant l'appel à Ollama.")
    except Exception as e:
        raise RuntimeError(f"💥 Erreur Ollama: {e}")

def ask_openai(prompt: str) -> str:
    """
    Interroge un modèle distant via l'API OpenAI.

    Args:
        prompt (str): Le prompt à envoyer.

    Returns:
        str: La réponse du modèle OpenAI.

    Raises:
        RuntimeError: Si la clé API est absente ou si la requête échoue.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("🔐 Clé API OpenAI manquante (OPENAI_API_KEY).")

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(f"💥 Erreur OpenAI: {e}")

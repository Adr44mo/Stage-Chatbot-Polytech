import subprocess
import openai
import os
from dotenv import load_dotenv

# Global configuration
OLLAMA_MODEL = "mistral"
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-3.5-turbo"
# Load environment variables from .env file in the same directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def ask_model(prompt: str, engine: str = "openai") -> str:
    if engine == "ollama":
        return ask_ollama(prompt)
    elif engine == "openai":
        return ask_openai(prompt)
    else:
        raise ValueError(f"❌ Unknown engine: {engine}")

def ask_ollama(prompt: str) -> str:
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
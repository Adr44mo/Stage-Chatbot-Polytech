import requests
import json
import uuid
import time
import openai
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI

import re

def clean_json_block(text):
    """
    Supprime les balises Markdown comme ```json ou ``` et retourne le JSON brut.
    """
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


# Charger les variables d'environnement
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


client = OpenAI()  # instancie le nouveau client


# Configuration
CHATBOT_URL = "http://localhost:8000/chat"  # À adapter si ton API est hébergée ailleurs
SESSION_ID = str(uuid.uuid4())
HEADERS = {
    "Content-Type": "application/json",
    "x-session-id": SESSION_ID
}

INPUT_FILE = "questions.json"
OUTPUT_FILE = "output.json"

print(f"Starting evaluation with session ID: {SESSION_ID}")

# Charger les questions
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    questions_with_answers = json.load(f)

results = []

# Boucle sur les questions
for item in questions_with_answers:
    prompt = item["question"]
    expected = item["reponse"]

    # Appel chatbot local
    chatbot_payload = {
        "prompt": prompt,
        "chat_history": []
    }

    try:
        chatbot_response = requests.post(CHATBOT_URL, headers=HEADERS, json=chatbot_payload)
        chatbot_answer = chatbot_response.json().get("answer", "")
    except Exception as e:
        chatbot_answer = f"Erreur lors de l'appel au chatbot : {e}"

    print(f"\nQ: {prompt}\nChatbot: {chatbot_answer}")

    # Appel OpenAI pour évaluer la réponse
    eval_prompt = f"""
    Tu es un correcteur pédagogique. Voici une question posée à un chatbot, la réponse attendue, et la réponse fournie par le chatbot. 
    Tu dois attribuer une **note sur 10** à la réponse du chatbot, et justifier brièvement.

    Rends ta réponse **uniquement au format JSON** suivant :
    {{
      "note": ENTIER_ENTRE_0_ET_10,
      "commentaire": "COMMENTAIRE_BREF"
    }}

    Question : {prompt}

    Réponse attendue : {expected}

    Réponse du chatbot : {chatbot_answer}
"""

    try:
        eval_response = client.chat.completions.create(
            model="gpt-4o",  # ou "gpt-4", "gpt-4o-mini" si disponible et souhaité
            messages=[
                {"role": "system", "content": "Tu es un évaluateur de qualité."},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.3
        )
        eval_content = eval_response.choices[0].message.content.strip()
        eval_cleaned = clean_json_block(eval_content)
        evaluation = json.loads(eval_cleaned)

    except Exception as e:
        evaluation = {"note": None, "commentaire": f"Erreur d'évaluation : {e}"}

    results.append({
        "question": prompt,
        "expected_answer": expected,
        "chatbot_answer": chatbot_answer,
        "evaluation": evaluation
    })

    time.sleep(1)  # Respecte le quota

# Sauvegarde
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n✅ Évaluation terminée. Résultats dans {OUTPUT_FILE}")

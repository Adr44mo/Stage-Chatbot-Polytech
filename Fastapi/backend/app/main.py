from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from llmm import initialize_the_rag_chain
from chat import format_sources
from filters import handle_if_uninformative

app = FastAPI()

# Autorise le frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, remplace par ["https://tonsite.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise la chaîne RAG une seule fois
rag_chain = initialize_the_rag_chain()

# === Modèle de requête & réponse ===

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str
    chat_history: List[Message]

class ChatResponse(BaseModel):
    answer: str
    sources: str

# === Endpoint principal ===

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Filtrage rapide si question trop vague
    filtered = handle_if_uninformative(request.prompt)
    if filtered:
        return ChatResponse(answer=filtered, sources="Aucune source identifiée")

    # Appel à la chaîne RAG
    response = rag_chain.invoke({
        "input": request.prompt,
        "chat_history": [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history if msg.role == "assistant"
        ],
    })

    answer = response.get("answer", "")
    sources = format_sources(response.get("context", []))

    return ChatResponse(answer=answer, sources=sources)

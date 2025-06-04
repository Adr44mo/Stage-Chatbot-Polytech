from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from .app.keys_file import OPENAI_API_KEY
from .app.llmm import initialize_the_rag_chain
from .app.chat import format_sources
from .app.filters import handle_if_uninformative


from .app.auth.router import router as auth_router
from .app.auth.database import create_db_and_tables


app = FastAPI()
print("[INFO] FastAPI app initialized")

# Autorise le frontend à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, remplace par ["https://tonsite.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
            for msg in request.chat_history if msg.role == "assistant" or msg.role == "user"
        ],
    })

    answer = response.get("answer", "")
    sources = format_sources(response.get("context", []))

    return ChatResponse(answer=answer, sources=sources)

import os

port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    print(f"[INFO] Starting FastAPI app on port {port}...")
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
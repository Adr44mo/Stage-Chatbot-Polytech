# =====================================================
# Point d'entrée principal de l'API pour le chatbot RAG
# =====================================================

# Imports des bibliothèques nécessaires
from fastapi import FastAPI, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

# Imports internes 
from .app.keys_file import OPENAI_API_KEY
from .app.llmm import initialize_the_rag_chain
from .app.chat import router as chat_router, get_sources, get_or_create_conversation, add_message
# from .app.filters import handle_if_uninformative
from .app.auth.router import router as auth_router
from .app.auth.database import create_db_and_tables, get_session
from .app.chat_models import ChatRequest, ChatResponse

# ==============
# Initialisation
# ==============

# Initialisation de l'application FastAPI
app = FastAPI()
print("[INFO] FastAPI app initialized")

# Configuration CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre à ton domaine
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs (authentification, chat/historique)
app.include_router(auth_router)
app.include_router(chat_router)

# Initialisation de la base de données au démarrage
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Initialisation de la chaîne RAG
rag_chain = initialize_the_rag_chain()

# ==========================
# Endpoint principal : /chat
# ==========================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_session_id: str = Header(...), session: Session = Depends(get_session)):
    """
    Endpoint principal pour le chatbot RAG : gestion des messages et historique de conversation.
    """
    
    # # Filtrage des requêtes non informatives (pas d'appels à l'API OpenAI)
    # filtered = handle_if_uninformative(request.prompt)
    # if filtered:
    #     return ChatResponse(answer=filtered, sources="Aucune source identifiée")

    conversation = get_or_create_conversation(session, x_session_id)
    add_message(session, conversation.id, "user", request.prompt)

    response = rag_chain.invoke({
        "input": request.prompt,
        "chat_history": [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history if msg.role == "assistant" or msg.role == "user"
        ],
    })

    answer = response.get("answer", "")
    sources = get_sources(response.get("context", []))

    add_message(session, conversation.id, "assistant", answer, sources)

    return ChatResponse(answer=answer, sources=sources)

# ==========================
# Lancement de l'application
# ==========================

import os
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    print(f"[INFO] Starting FastAPI app on port {port}...")
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)

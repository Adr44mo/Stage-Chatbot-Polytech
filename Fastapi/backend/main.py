# =====================================================
# Point d'entrée principal de l'API pour le chatbot RAG
# =====================================================

# Imports des bibliothèques nécessaires
from fastapi import FastAPI, Depends, Request, Response, Cookie, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from redis import Redis
from sqlmodel import Session
from datetime import datetime, timedelta
import uuid
import os

from color_utils import ColorPrint

cp = ColorPrint()

# Imports internes 
from .app.keys_file import OPENAI_API_KEY
from .app.llmm import initialize_the_rag_chain
from .app.chat import router as chat_router, get_sources, get_or_create_conversation, add_message
from .app.recaptcha import verify_recaptcha_token
from .app.server_file import router as server_router
from Document_handler.The_handler import router as router_scrapping
from .app.PDF_manual.pdf_manual import router as pdf_manual_router
# from .app.filters import handle_if_uninformative
from .app.auth.router import router as auth_router
from .app.auth.database import create_db_and_tables, get_session
from .app.chat_models import ChatRequest, ChatResponse
from .app.auth.dependencies import get_current_admin
from .app.intelligent_rag.api import router as intelligent_rag_router
from .app.intelligent_rag.db_routes import router as db_router

# ==============================
# Configuration des systèmes RAG
# ==============================

# Variables de configuration 
USE_INTELLIGENT_RAG = True   # Système RAG intelligent (nouvelle version)
USE_LANGGRAPH = True         # LangGraph RAG system 
# Note: Si USE_INTELLIGENT_RAG est True, il a la priorité sur USE_LANGGRAPH

def get_rag_system_info():
    """Retourne des informations sur le système RAG utilisé"""
    if USE_INTELLIGENT_RAG:
        return "Intelligent RAG (avec analyse d'intention et routage)"
    elif USE_LANGGRAPH:
        return "LangGraph RAG"
    else:
        return "Classic RAG"

# =================
# Test de LangGraph
# =================

if USE_INTELLIGENT_RAG:
    from .app.intelligent_rag.graph import invoke_intelligent_rag
    cp.print_info(f"{get_rag_system_info()}")
elif USE_LANGGRAPH:
    from .app.langgraph_system.rag_graph import invoke_langgraph_rag
    cp.print_info(f"{get_rag_system_info()}")
else:
    cp.print_info(f"{get_rag_system_info()}")

# ============================================
# Initialisation de FastAPI (et rate limiting)
# ============================================

# Initialisation de l'application FastAPI
app = FastAPI()
cp.print_info("FastAPI app initialized")

# Initialisation du limiteur de requêtes (avec Redis comme stockage)
redis = Redis(host="localhost", port = 6379, decode_responses=True)
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def session_id_key(request: Request):
    """
    Retourne le session_id du cookie si présent, sinon l’IP.
    """
    return request.cookies.get("polybot_session_id") or get_remote_address(request)

# ==============
# Initialisation
# ==============

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
app.include_router(server_router)
app.include_router(router_scrapping, prefix="/scraping", tags=["Scraping"])#, dependencies=[Depends(get_current_admin)])
app.include_router(pdf_manual_router, prefix="/pdf_manual", tags=["PDF Manual"])#, dependencies=[Depends(get_current_admin)])
app.include_router(intelligent_rag_router)  # Nouveau système RAG intelligent
app.include_router(db_router)  # Routes pour la base de données RAG

# Initialisation de la base de données au démarrage
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Initialisation de la chaîne RAG
rag_chain = initialize_the_rag_chain()

# ====================================
# Endpoint d'initialisation de session
# ====================================

@app.get("/init-session")
def init_session(response: Response, polybot_session_id: str = Cookie(None)):
    if polybot_session_id:
        return {"ok": True}
    session_id = str(uuid.uuid4())
    expire_date = datetime.utcnow() + timedelta(days=180)
    response.set_cookie(
        key="polybot_session_id",
        value=session_id,
        httponly=True,
        max_age=60*60*24*180,  # 6 mois
        expires=expire_date.strftime("%a, %d-%b-%Y %H:%M:%S GMT"),
        samesite="lax",
        secure=False  # True si HTTPS
    )
    return {"ok": True}

# ==========================
# Endpoint principal : /chat
# ==========================

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/second")  # Limite par IP (clé par défaut)
@limiter.limit("1/second", key_func=session_id_key)  # Limite par session_id 
async def chat(request: Request, request_body: ChatRequest, polybot_session_id: str = Cookie(None), session: Session = Depends(get_session)):
    """
    Endpoint principal pour le chatbot RAG : gestion des messages et historique de conversation.
    """
    # Vérification reCAPTCHA
    if not request_body.recaptcha_token:
        raise HTTPException(status_code=400, detail="reCAPTCHA token required")
    if not await verify_recaptcha_token(request_body.recaptcha_token):
        raise HTTPException(status_code=400, detail="Invalid reCAPTCHA token")

    conversation = get_or_create_conversation(session, polybot_session_id)
    add_message(session, conversation.id, "user", request_body.prompt)

    # ====================================================
    # TEST : Intelligent RAG vs LangGraph vs RAG classique
    # ====================================================

    if USE_INTELLIGENT_RAG:
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request_body.chat_history if msg.role == "assistant" or msg.role == "user"
        ]
        
        response = invoke_intelligent_rag(request_body.prompt, chat_history)
        
        answer = response.get("answer", "")
        context = response.get("context", [])
        sources = response.get("sources", [])
        
    elif USE_LANGGRAPH:
        response = invoke_langgraph_rag({
            "input": request_body.prompt,
            "chat_history": [
                {"role": msg.role, "content": msg.content}
                for msg in request_body.chat_history if msg.role == "assistant" or msg.role == "user"
            ],
        })
        
        answer = response.get("answer", "")
        context = response.get("context", [])
        sources = get_sources(context) if context else []
        
    else:
        response = rag_chain.invoke({
            "input": request_body.prompt,
            "chat_history": [
                {"role": msg.role, "content": msg.content}
                for msg in request_body.chat_history if msg.role == "assistant" or msg.role == "user"
            ],
        })
        
        answer = response.get("answer", "")
        context = response.get("context", [])
        sources = get_sources(context) if context else []

    add_message(session, conversation.id, "assistant", answer, sources)

    return ChatResponse(answer=answer, sources=sources)

# =========================================================
# Endpoint pour obtenir des informations sur le système RAG
# =========================================================

@app.get("/system-info")
def get_system_info():
    """
    Endpoint pour obtenir des informations sur le système RAG actuellement utilisé
    """
    return {
        "rag_system": get_rag_system_info(),
        "use_intelligent_rag": USE_INTELLIGENT_RAG,
        "use_langgraph": USE_LANGGRAPH,
        "timestamp": datetime.utcnow().isoformat()
    }

# ==========================
# Lancement de l'application
# ==========================

import os
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    cp.print_info(f"Starting FastAPI app on port {port}...")
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)

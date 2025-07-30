#!/bin/bash

# =============================================================================
# Script d'arrêt propre pour Stage-Chatbot-Polytech
# =============================================================================
# Arrête le backend (uvicorn) et Nginx, nettoie le fichier PID

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}
log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}
log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

PROJECT_ROOT="$(pwd)"
PID_FILE="$PROJECT_ROOT/app.pid"

log_info "Arrêt du backend (uvicorn)..."
if [[ -f "$PID_FILE" ]]; then
    BACKEND_PID=$(cat "$PID_FILE")
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill -TERM $BACKEND_PID
        sleep 5
        kill -KILL $BACKEND_PID 2>/dev/null || true
        log_success "Backend arrêté (PID: $BACKEND_PID)"
    else
        log_warning "Processus backend déjà arrêté"
    fi
    rm -f "$PID_FILE"
else
    pkill -f uvicorn 2>/dev/null || true
    log_warning "Fichier PID absent, kill uvicorn global"
fi

log_info "Arrêt de Nginx..."
sudo systemctl stop nginx 2>/dev/null || true
sudo pkill -f nginx 2>/dev/null || true
log_success "Nginx arrêté"

log_success "Arrêt complet terminé."

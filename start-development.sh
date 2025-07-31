#!/bin/bash

# =============================================================================
# Script de démarrage DÉVELOPPEMENT pour Stage-Chatbot-Polytech
# =============================================================================
# - Configuration optimisée pour développement avec HTTPS
# - Hot reload activé pour le frontend et backend
# - Logs en temps réel
# - Pas de redémarrage automatique (mode dev)

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

# =============================================================================
# CONFIGURATION DÉVELOPPEMENT
# =============================================================================

PROJECT_ROOT="$(pwd)"
CONFIG_FILE="$PROJECT_ROOT/config.env"

# Vérification et chargement de la configuration
if [[ ! -f "$CONFIG_FILE" ]]; then
    log_error "Fichier de configuration manquant: $CONFIG_FILE"
    log_error "Lancez d'abord: ./init.sh"
    exit 1
fi

# Charger la configuration
source "$CONFIG_FILE"

# Validation des variables critiques
if [[ -z "$OPENAI_API_KEY" ]]; then
    log_warning "OPENAI_API_KEY non définie dans $CONFIG_FILE"
fi

if [[ -z "$SERVER_DOMAIN" ]]; then
    log_warning "SERVER_DOMAIN non définie, utilisation de 'localhost'"
    SERVER_DOMAIN="localhost"
fi

# Variables dérivées de la configuration
VENV_PATH="$PROJECT_ROOT/.venv/bin/activate"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE_BACKEND="$PROJECT_ROOT/backend-dev.pid"
PID_FILE_FRONTEND="$PROJECT_ROOT/frontend-dev.pid"

# Utiliser les valeurs du fichier config ou valeurs par défaut pour développement
BACKEND_PORT=${BACKEND_PORT:-8000}           # Par défaut port 8000
FRONTEND_PORT=${FRONTEND_PORT:-5173}         # Par défaut port 5173 (Vite)
SERVER_DOMAIN=${SERVER_DOMAIN:-localhost}   # Par défaut localhost
LOG_LEVEL=${LOG_LEVEL:-debug}                # Mode debug pour développement

# =============================================================================
# NETTOYAGE ET PRÉPARATION
# =============================================================================

cleanup_processes() {
    log_info "🧹 Nettoyage des processus existants..."
    
    # Kill processus existants
    pkill -f uvicorn 2>/dev/null || true
    pkill -f vite 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    
    # Attendre que les processus soient terminés
    sleep 2
    
    # Force kill des ports si nécessaire
    if lsof -i :$BACKEND_PORT >/dev/null 2>&1; then
        log_warning "Port $BACKEND_PORT encore occupé, force kill..."
        fuser -k $BACKEND_PORT/tcp 2>/dev/null || true
        sleep 1
    fi
    
    if lsof -i :$FRONTEND_PORT >/dev/null 2>&1; then
        log_warning "Port $FRONTEND_PORT encore occupé, force kill..."
        fuser -k $FRONTEND_PORT/tcp 2>/dev/null || true
        sleep 1
    fi
    
    # Nettoyer les fichiers PID
    rm -f "$PID_FILE_BACKEND" "$PID_FILE_FRONTEND"
    
    log_success "Nettoyage terminé"
}

setup_logs() {
    log_info "📁 Configuration des logs..."
    
    # Créer le répertoire de logs
    mkdir -p "$LOG_DIR"
    
    # Rotation des logs si nécessaire (plus petite limite en dev)
    if [[ -f "$LOG_DIR/backend-dev.log" ]] && [[ $(stat -c%s "$LOG_DIR/backend-dev.log") -gt 5242880 ]]; then
        mv "$LOG_DIR/backend-dev.log" "$LOG_DIR/backend-dev.log.$(date +%Y%m%d_%H%M%S)"
        log_info "Log backend dev archivé (>5MB)"
    fi
    
    if [[ -f "$LOG_DIR/frontend-dev.log" ]] && [[ $(stat -c%s "$LOG_DIR/frontend-dev.log") -gt 5242880 ]]; then
        mv "$LOG_DIR/frontend-dev.log" "$LOG_DIR/frontend-dev.log.$(date +%Y%m%d_%H%M%S)"
        log_info "Log frontend dev archivé (>5MB)"
    fi
    
    log_success "Logs configurés"
}

# =============================================================================
# DÉMARRAGE NGINX DÉVELOPPEMENT
# =============================================================================

start_nginx_dev() {
    log_info "🌐 Configuration Nginx HTTPS (développement)..."
    
    # D'abord générer/régénérer la configuration nginx
    log_info "Génération de la configuration nginx..."
    if [[ -f "$PROJECT_ROOT/nginx-setup.sh" ]]; then
        sudo "$PROJECT_ROOT/nginx-setup.sh"
    else
        log_error "Script nginx-setup.sh introuvable"
        exit 1
    fi
    
    # Déterminer le fichier de configuration à utiliser
    NGINX_CONFIG_FILE="$PROJECT_ROOT/Fastapi/nginx/nginx-https-configured.conf"
    
    # Vérifier que le fichier de configuration existe
    if [[ ! -f "$NGINX_CONFIG_FILE" ]]; then
        log_error "Configuration Nginx développement manquante: $NGINX_CONFIG_FILE"
        log_error "Le script nginx-setup.sh a échoué"
        exit 1
    fi
    
    # Tester la configuration et afficher le warning ssl_stapling si présent
    NGINX_OUTPUT=$(sudo nginx -t -c "$NGINX_CONFIG_FILE" 2>&1)
    echo "$NGINX_OUTPUT" | grep -q 'ssl_stapling' && {
        log_warning "Nginx : warning ssl_stapling ignoré (certificat auto-signé)"
        log_info "Ce warning est normal avec un certificat auto-signé et n'affecte pas le fonctionnement HTTPS."
    }
    
    if echo "$NGINX_OUTPUT" | grep -q 'syntax is ok' && echo "$NGINX_OUTPUT" | grep -q 'test is successful'; then
        # Stopper nginx existant
        sudo systemctl stop nginx 2>/dev/null || true
        sudo pkill -f nginx 2>/dev/null || true
        sleep 1
        
        # Démarrer nginx avec config DÉVELOPPEMENT
        sudo nginx -c "$NGINX_CONFIG_FILE"
        if ! pgrep nginx >/dev/null; then
            log_error "Échec du démarrage de Nginx"
            exit 1
        fi
        log_success "Nginx DÉVELOPPEMENT démarré (HTTPS sur port 443, proxy vers frontend:$FRONTEND_PORT et backend:$BACKEND_PORT)"
    else
        log_error "Configuration Nginx invalide"
        echo "$NGINX_OUTPUT"
        exit 1
    fi
}

# =============================================================================
# DÉMARRAGE BACKEND DÉVELOPPEMENT
# =============================================================================

start_backend_dev() {
    log_info "🚀 Démarrage backend développement (hot reload activé)..."
    
    # Vérifier l'environnement virtuel
    if [[ ! -f "$VENV_PATH" ]]; then
        log_error "Environnement virtuel introuvable à $VENV_PATH"
        exit 1
    fi
    
    source "$VENV_PATH"
    cd "$PROJECT_ROOT"
    
    # Démarrage uvicorn en mode développement avec reload
    log_info "Démarrage uvicorn avec hot reload sur port $BACKEND_PORT..."
    uvicorn Fastapi.backend.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        --log-level $LOG_LEVEL \
        --access-log \
        >> "$LOG_DIR/backend-dev.log" 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PID_FILE_BACKEND"
    
    # Vérifier que le backend a bien démarré
    sleep 3
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "Échec du démarrage du backend"
        log_error "Logs:"
        tail -20 "$LOG_DIR/backend-dev.log" || echo "Pas de logs disponibles"
        exit 1
    fi
    
    log_success "Backend développement démarré (PID: $BACKEND_PID, hot reload actif)"
}

# =============================================================================
# DÉMARRAGE FRONTEND DÉVELOPPEMENT
# =============================================================================

start_frontend_dev() {
    log_info "🎨 Démarrage frontend développement (hot reload activé)..."
    
    cd "$PROJECT_ROOT/Fastapi/frontend"
    
    # Installation des dépendances si nécessaire
    if [[ ! -d "node_modules" ]] || [[ package.json -nt node_modules ]]; then
        log_info "Installation des dépendances npm..."
        npm install
    fi
    
    # Démarrer le serveur de développement Vite
    log_info "Démarrage du serveur Vite sur port $FRONTEND_PORT..."
    npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT \
        >> "$LOG_DIR/frontend-dev.log" 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PID_FILE_FRONTEND"
    
    # Vérifier que le frontend a bien démarré
    sleep 5
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        log_error "Échec du démarrage du frontend"
        log_error "Logs:"
        tail -20 "$LOG_DIR/frontend-dev.log" || echo "Pas de logs disponibles"
        exit 1
    fi
    
    log_success "Frontend développement démarré (PID: $FRONTEND_PID, hot reload actif)"
    
    # Retourner au répertoire racine
    cd "$PROJECT_ROOT"
}

# =============================================================================
# MONITORING DÉVELOPPEMENT
# =============================================================================

setup_monitoring_dev() {
    log_info "📊 Configuration du monitoring développement..."
    
    # Script de monitoring pour développement
    cat > "$PROJECT_ROOT/monitor-dev.sh" << EOF
#!/bin/bash

PROJECT_ROOT="$PROJECT_ROOT"
LOG_DIR="$PROJECT_ROOT/logs"

# Charger la configuration
CONFIG_FILE="$PROJECT_ROOT/config.env"
if [[ -f "\$CONFIG_FILE" ]]; then
    source "\$CONFIG_FILE"
fi

# Variables par défaut si config non trouvée
BACKEND_PORT=\${BACKEND_PORT:-8000}
FRONTEND_PORT=\${FRONTEND_PORT:-5173}
SERVER_DOMAIN=\${SERVER_DOMAIN:-localhost}

echo "=== MONITORING DÉVELOPPEMENT STAGE-CHATBOT-POLYTECH ==="
echo "Date: \$(date)"
echo "Configuration: \$SERVER_DOMAIN | Backend: \$BACKEND_PORT | Frontend: \$FRONTEND_PORT"
echo

# Status Nginx
echo "🌐 NGINX:"
if pgrep nginx >/dev/null; then
    echo "  ✅ Actif (HTTPS sur port 443)"
    echo "  Connexions: \$(ss -tuln | grep :443 | wc -l) sur port 443"
else
    echo "  ❌ Arrêté"
fi
echo

# Status Backend
echo "🚀 BACKEND (Développement):"
if pgrep -f "uvicorn.*--reload" >/dev/null; then
    echo "  ✅ Actif avec hot reload (port \$BACKEND_PORT)"
    echo "  PID: \$(pgrep -f "uvicorn.*--reload")"
    echo "  Mémoire: \$(ps -o pid,ppid,pcpu,pmem,cmd -p \$(pgrep -f "uvicorn.*--reload") | tail -n +2 | head -1)"
else
    echo "  ❌ Arrêté"
fi
echo

# Status Frontend
echo "🎨 FRONTEND (Développement):"
if pgrep -f "vite.*dev" >/dev/null || pgrep -f "npm run dev" >/dev/null; then
    echo "  ✅ Actif avec hot reload (port \$FRONTEND_PORT)"
    echo "  PID: \$(pgrep -f "vite.*dev\|npm run dev")"
else
    echo "  ❌ Arrêté"
fi
echo

# Logs récents
echo "📝 LOGS RÉCENTS:"
echo "Backend (dernières 10 lignes):"
if [[ -f "\$LOG_DIR/backend-dev.log" ]]; then
    tail -10 "\$LOG_DIR/backend-dev.log" | sed 's/^/  /'
else
    echo "  Pas de logs backend"
fi
echo
echo "Frontend (dernières 10 lignes):"
if [[ -f "\$LOG_DIR/frontend-dev.log" ]]; then
    tail -10 "\$LOG_DIR/frontend-dev.log" | sed 's/^/  /'
else
    echo "  Pas de logs frontend"
fi
echo

# Connexions actives
echo "🔗 CONNEXIONS ACTIVES:"
ss -tuln | grep -E ":(443|\$BACKEND_PORT|\$FRONTEND_PORT)" | sed 's/^/  /' || echo "  Aucune connexion"

EOF
    
    chmod +x "$PROJECT_ROOT/monitor-dev.sh"
    
    log_success "Script de monitoring développement créé: $PROJECT_ROOT/monitor-dev.sh"
}

# =============================================================================
# GESTION DES SIGNAUX ET ARRÊT PROPRE
# =============================================================================

setup_signal_handlers() {
    # Gestionnaire d'arrêt propre
    cleanup_and_exit() {
        log_info "🛑 Arrêt demandé, nettoyage en cours..."
        
        # Arrêter le backend
        if [[ -f "$PID_FILE_BACKEND" ]]; then
            BACKEND_PID=$(cat "$PID_FILE_BACKEND")
            if kill -0 $BACKEND_PID 2>/dev/null; then
                log_info "Arrêt du backend (PID: $BACKEND_PID)..."
                kill -TERM $BACKEND_PID
                sleep 3
                kill -KILL $BACKEND_PID 2>/dev/null || true
            fi
            rm -f "$PID_FILE_BACKEND"
        fi
        
        # Arrêter le frontend
        if [[ -f "$PID_FILE_FRONTEND" ]]; then
            FRONTEND_PID=$(cat "$PID_FILE_FRONTEND")
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                log_info "Arrêt du frontend (PID: $FRONTEND_PID)..."
                kill -TERM $FRONTEND_PID
                sleep 3
                kill -KILL $FRONTEND_PID 2>/dev/null || true
            fi
            rm -f "$PID_FILE_FRONTEND"
        fi
        
        # Arrêter nginx
        log_info "Arrêt de Nginx..."
        sudo systemctl stop nginx 2>/dev/null || true
        
        log_success "Arrêt propre terminé"
        exit 0
    }
    
    # Capturer les signaux
    trap cleanup_and_exit SIGTERM SIGINT
}

# =============================================================================
# SURVEILLANCE DES LOGS EN TEMPS RÉEL
# =============================================================================

start_log_monitoring() {
    log_info "📊 Démarrage de la surveillance des logs en temps réel..."
    
    # Fonction pour afficher les logs en temps réel
    monitor_logs() {
        # Attendre que les logs soient créés
        sleep 5
        
        log_info "=== LOGS EN TEMPS RÉEL ==="
        log_info "Backend: tail -f $LOG_DIR/backend-dev.log"
        log_info "Frontend: tail -f $LOG_DIR/frontend-dev.log"
        log_info "Pour arrêter: Ctrl+C"
        echo
        
        # Suivre les logs en parallèle
        if [[ -f "$LOG_DIR/backend-dev.log" ]] && [[ -f "$LOG_DIR/frontend-dev.log" ]]; then
            tail -f "$LOG_DIR/backend-dev.log" "$LOG_DIR/frontend-dev.log" &
            LOG_TAIL_PID=$!
        elif [[ -f "$LOG_DIR/backend-dev.log" ]]; then
            tail -f "$LOG_DIR/backend-dev.log" &
            LOG_TAIL_PID=$!
        elif [[ -f "$LOG_DIR/frontend-dev.log" ]]; then
            tail -f "$LOG_DIR/frontend-dev.log" &
            LOG_TAIL_PID=$!
        fi
        
        # Attendre indéfiniment (les signaux géreront l'arrêt)
        wait
    }
    
    monitor_logs
}

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

main() {
    log_info "🚀 DÉMARRAGE DÉVELOPPEMENT - Stage-Chatbot-Polytech"
    log_info "=============================================="
    
    # Vérifications
    if [[ $EUID -eq 0 ]]; then
        log_error "Ne pas exécuter en tant que root"
        exit 1
    fi
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Fichier config.env manquant. Lancez d'abord ./init.sh"
        exit 1
    fi
    
    # Afficher la configuration chargée
    log_info "Configuration chargée depuis: $CONFIG_FILE"
    log_info "  - Serveur: $SERVER_DOMAIN"
    log_info "  - Port backend: $BACKEND_PORT (hot reload)"
    log_info "  - Port frontend: $FRONTEND_PORT (hot reload)"
    log_info "  - Log level: $LOG_LEVEL"
    echo
    
    # Configuration des gestionnaires de signaux
    setup_signal_handlers
    
    # Préparation
    cleanup_processes
    setup_logs
    setup_monitoring_dev
    
    # Démarrage des services
    start_nginx_dev
    start_backend_dev
    start_frontend_dev
    
    # Affichage des informations
    log_success "🎉 DÉVELOPPEMENT DÉMARRÉ"
    echo
    log_info "=== ACCÈS ==="
    log_info "Interface: https://$SERVER_DOMAIN:443"
    log_info "API: https://$SERVER_DOMAIN:443/api/"
    log_info "Frontend direct: http://$SERVER_DOMAIN:$FRONTEND_PORT (dev server)"
    log_info "Backend direct: http://$SERVER_DOMAIN:$BACKEND_PORT (API)"
    echo
    log_info "=== MONITORING ==="
    log_info "Status: ./monitor-dev.sh"
    log_info "Logs backend: tail -f $LOG_DIR/backend-dev.log"
    log_info "Logs frontend: tail -f $LOG_DIR/frontend-dev.log"
    echo
    log_info "=== DÉVELOPPEMENT ==="
    log_info "Hot reload activé pour backend et frontend"
    log_info "Les modifications de code sont automatiquement rechargées"
    log_info "Pour arrêter: Ctrl+C"
    echo
    
    # Démarrage de la surveillance des logs (bloquant)
    start_log_monitoring
}

# Exécution
main "$@"

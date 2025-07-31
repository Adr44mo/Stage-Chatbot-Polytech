#!/bin/bash

# =============================================================================
# Script de démarrage PRODUCTION pour Stage-Chatbot-Polytech
# =============================================================================
# - Configuration optimisée pour production
# - Redémarrage automatique d'uvicorn toutes les heures pour vider le cache
# - Logs structurés et monitoring
# - Pas de --reload (mode production)

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
# CONFIGURATION PRODUCTION
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
PID_FILE="$PROJECT_ROOT/app.pid"

# Utiliser les valeurs du fichier config ou valeurs par défaut
RESTART_INTERVAL=${RESTART_INTERVAL:-3600}  # Par défaut 1 heure
WORKERS=${WORKERS:-2}                        # Par défaut 2 workers
BACKEND_PORT=${BACKEND_PORT:-8000}           # Par défaut port 8000
SERVER_DOMAIN=${SERVER_DOMAIN:-localhost}   # Par défaut localhost
LOG_LEVEL=${LOG_LEVEL:-info}                 # Par défaut info

# =============================================================================
# NETTOYAGE ET PRÉPARATION
# =============================================================================

cleanup_processes() {
    log_info "🧹 Nettoyage des processus existants..."
    
    # Kill processus existants
    pkill -f uvicorn 2>/dev/null || true
    pkill -f vite 2>/dev/null || true
    
    # Attendre que les processus soient terminés
    sleep 2
    
    # Force kill des ports si nécessaire
    if lsof -i :$BACKEND_PORT >/dev/null 2>&1; then
        log_warning "Port $BACKEND_PORT encore occupé, force kill..."
        fuser -k $BACKEND_PORT/tcp 2>/dev/null || true
        sleep 1
    fi
    
    if lsof -i :5173 >/dev/null 2>&1; then
        log_warning "Port 5173 encore occupé, force kill..."
        fuser -k 5173/tcp 2>/dev/null || true
        sleep 1
    fi
    
    # Nettoyer le fichier PID
    rm -f "$PID_FILE"
    
    log_success "Nettoyage terminé"
}

setup_logs() {
    log_info "📁 Configuration des logs..."
    
    # Créer le répertoire de logs
    mkdir -p "$LOG_DIR"
    
    # Rotation des logs si nécessaire
    if [[ -f "$LOG_DIR/backend.log" ]] && [[ $(stat -c%s "$LOG_DIR/backend.log") -gt 10485760 ]]; then
        mv "$LOG_DIR/backend.log" "$LOG_DIR/backend.log.$(date +%Y%m%d_%H%M%S)"
        log_info "Log backend archivé (>10MB)"
    fi
    
    if [[ -f "$LOG_DIR/frontend.log" ]] && [[ $(stat -c%s "$LOG_DIR/frontend.log") -gt 10485760 ]]; then
        mv "$LOG_DIR/frontend.log" "$LOG_DIR/frontend.log.$(date +%Y%m%d_%H%M%S)"
        log_info "Log frontend archivé (>10MB)"
    fi
    
    log_success "Logs configurés"
}

# =============================================================================
# DÉMARRAGE NGINX
# =============================================================================

start_nginx() {
    log_info "🌐 Configuration Nginx HTTPS (production)..."
    
    # Déterminer le fichier de configuration à utiliser
    NGINX_CONFIG_FILE="$PROJECT_ROOT/Fastapi/nginx/nginx-production-configured.conf"
    
    # Vérifier que le fichier de configuration existe (créé par init.sh)
    if [[ ! -f "$NGINX_CONFIG_FILE" ]]; then
        log_error "Configuration Nginx production manquante: $NGINX_CONFIG_FILE"
        log_error "Lancez d'abord: ./init.sh avec DEPLOYMENT_MODE=production"
        exit 1
    fi
    
    # Tester la configuration et afficher le warning ssl_stapling si présent
    NGINX_OUTPUT=$(sudo nginx -t -c "$NGINX_CONFIG_FILE" 2>&1)
    echo "$NGINX_OUTPUT" | grep -q 'ssl_stapling' && {
        log_warning "Nginx : warning ssl_stapling ignoré (certificat auto-signé ou intermédiaire manquant)"
        log_info "Ce warning est normal avec un certificat auto-signé et n'affecte pas le fonctionnement HTTPS."
    }
    if echo "$NGINX_OUTPUT" | grep -q 'syntax is ok' && echo "$NGINX_OUTPUT" | grep -q 'test is successful'; then
        # Stopper nginx existant
        sudo systemctl stop nginx 2>/dev/null || true
        sudo pkill -f nginx 2>/dev/null || true
        sleep 1
        # Démarrer nginx avec config PRODUCTION
        sudo nginx -c "$NGINX_CONFIG_FILE"
        if ! pgrep nginx >/dev/null; then
            log_error "Échec du démarrage de Nginx"
            exit 1
        fi
        log_success "Nginx PRODUCTION démarré (fichiers statiques + port 443 exposé)"
    else
        log_error "Configuration Nginx invalide"
        echo "$NGINX_OUTPUT"
        exit 1
    fi
}

# =============================================================================
# DÉMARRAGE BACKEND AVEC REDÉMARRAGE AUTOMATIQUE
# =============================================================================

start_backend_with_restart() {
    log_info "🚀 Démarrage backend avec redémarrage automatique (${RESTART_INTERVAL}s)..."
    
    # Vérifier l'environnement virtuel
    if [[ ! -f "$VENV_PATH" ]]; then
        log_error "Environnement virtuel introuvable à $VENV_PATH"
        exit 1
    fi
    
    # Fonction pour démarrer uvicorn
    start_uvicorn() {
        log_info "Démarrage uvicorn (workers: $WORKERS)..."
        source "$VENV_PATH"
        
        cd "$PROJECT_ROOT"
        
        # Démarrage uvicorn en mode production (redirection des logs)
        uvicorn Fastapi.backend.main:app \
            --host 0.0.0.0 \
            --port $BACKEND_PORT \
            --workers $WORKERS \
            --log-level $LOG_LEVEL \
            --access-log \
            >> "$LOG_DIR/backend.log" 2>&1 &
        
        BACKEND_PID=$!
        echo $BACKEND_PID > "$PID_FILE"
        
        log_success "Backend démarré (PID: $BACKEND_PID)"
        return $BACKEND_PID
    }
    
    # Boucle de redémarrage automatique
    while true; do
        # Démarrer uvicorn
        start_uvicorn
        BACKEND_PID=$!
        
        # Attendre l'intervalle de redémarrage
        log_info "Prochain redémarrage dans ${RESTART_INTERVAL}s pour vider le cache..."
        sleep $RESTART_INTERVAL
        
        # Redémarrage gracieux
        log_info "🔄 Redémarrage gracieux du backend..."
        if kill -TERM $BACKEND_PID 2>/dev/null; then
            # Attendre que le processus se termine proprement
            for i in {1..10}; do
                if ! kill -0 $BACKEND_PID 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # Force kill si nécessaire
            kill -KILL $BACKEND_PID 2>/dev/null || true
        fi
        
        log_success "Backend redémarré (cache vidé)"
        sleep 2
    done
}

# =============================================================================
# DÉMARRAGE FRONTEND (BUILD PRODUCTION)
# =============================================================================

start_frontend_production() {
    log_info "🎨 Préparation frontend (production)..."
    
    cd "$PROJECT_ROOT/Fastapi/frontend"
    
    # Installation des dépendances
    if [[ ! -d "node_modules" ]] || [[ package.json -nt node_modules ]]; then
        log_info "Installation des dépendances npm..."
        npm ci --only=production
    fi
    
    # Build pour production
    log_info "Build production du frontend..."
    npm run build >> "$LOG_DIR/frontend.log" 2>&1
    
    if [[ ! -d "dist" ]]; then
        log_error "Build frontend échoué - dossier dist manquant"
        exit 1
    fi
    
    log_success "Frontend buildé pour production (servi par Nginx)"
    
    # Retourner au répertoire racine
    cd "$PROJECT_ROOT"
}

# =============================================================================
# MONITORING ET SANTÉ
# =============================================================================

setup_monitoring() {
    log_info "📊 Configuration du monitoring..."
    
    # Script de monitoring
    cat > "$PROJECT_ROOT/monitor.sh" << EOF
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
SERVER_DOMAIN=\${SERVER_DOMAIN:-localhost}
WORKERS=\${WORKERS:-2}
RESTART_INTERVAL=\${RESTART_INTERVAL:-3600}

echo "=== MONITORING STAGE-CHATBOT-POLYTECH ==="
echo "Date: \$(date)"
echo "Configuration: \$SERVER_DOMAIN | Workers: \$WORKERS | Port: \$BACKEND_PORT"
echo

# Status Nginx
echo "🌐 NGINX:"
if pgrep nginx >/dev/null; then
    echo "  ✅ Actif"
    echo "  Connexions: \$(ss -tuln | grep :443 | wc -l) sur port 443"
else
    echo "  ❌ Arrêté"
fi
echo

# Status Backend
echo "🚀 BACKEND:"
if pgrep -f uvicorn >/dev/null; then
    echo "  ✅ Actif (port \$BACKEND_PORT)"
    echo "  Processus: \$(pgrep -f uvicorn | wc -l)"
    echo "  Redémarrage auto: \${RESTART_INTERVAL}s"
    echo "  Mémoire: \$(ps -o pid,ppid,pcpu,pmem,cmd -p \$(pgrep -f uvicorn) | tail -n +2)"
else
    echo "  ❌ Arrêté"
fi
echo

# Logs récents
echo "📝 LOGS RÉCENTS:"
if [[ -f "\$LOG_DIR/backend.log" ]]; then
    echo "Backend (dernières 15 lignes):"
    tail -15 "\$LOG_DIR/backend.log" | sed 's/^/  /'
else
    echo "  Pas de logs backend"
fi
echo

# Utilisation disque
echo "💾 ESPACE DISQUE:"
df -h "\$PROJECT_ROOT" | tail -1 | awk '{print "  Utilisé: " \$3 "/" \$2 " (" \$5 ")"}'
echo

# Connexions actives
echo "🔗 CONNEXIONS ACTIVES:"
ss -tuln | grep -E ":(443|\$BACKEND_PORT|5173)" | sed 's/^/  /' || echo "  Aucune connexion"

EOF
    
    chmod +x "$PROJECT_ROOT/monitor.sh"
    
    log_success "Script de monitoring créé: $PROJECT_ROOT/monitor.sh"
}

# =============================================================================
# GESTION DES SIGNAUX ET ARRÊT PROPRE
# =============================================================================

setup_signal_handlers() {
    # Gestionnaire d'arrêt propre
    cleanup_and_exit() {
        log_info "🛑 Arrêt demandé, nettoyage en cours..."
        
        # Arrêter le backend
        if [[ -f "$PID_FILE" ]]; then
            BACKEND_PID=$(cat "$PID_FILE")
            if kill -0 $BACKEND_PID 2>/dev/null; then
                log_info "Arrêt du backend (PID: $BACKEND_PID)..."
                kill -TERM $BACKEND_PID
                sleep 5
                kill -KILL $BACKEND_PID 2>/dev/null || true
            fi
            rm -f "$PID_FILE"
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
# FONCTION PRINCIPALE
# =============================================================================

main() {
    log_info "🚀 DÉMARRAGE PRODUCTION - Stage-Chatbot-Polytech"
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
    log_info "  - Workers: $WORKERS"
    log_info "  - Port backend: $BACKEND_PORT"
    log_info "  - Redémarrage: ${RESTART_INTERVAL}s"
    echo
    
    # Configuration des gestionnaires de signaux
    setup_signal_handlers
    
    # Préparation
    cleanup_processes
    setup_logs
    setup_monitoring
    
    # Démarrage des services
    start_nginx
    start_frontend_production
    
    # Affichage des informations
    log_success "🎉 PRODUCTION DÉMARRÉE"
    echo
    log_info "=== ACCÈS ==="
    log_info "Interface: https://$SERVER_DOMAIN:443"
    log_info "API: https://$SERVER_DOMAIN:443/api/"
    echo
    log_info "=== MONITORING ==="
    log_info "Status: ./monitor.sh"
    log_info "Logs backend: tail -f $LOG_DIR/backend.log"
    log_info "Logs frontend: tail -f $LOG_DIR/frontend.log"
    echo
    log_info "=== REDÉMARRAGE AUTOMATIQUE ==="
    log_info "Backend redémarre toutes les ${RESTART_INTERVAL}s pour vider le cache"
    log_info "Pour arrêter: Ctrl+C ou kill $(echo $$)"
    echo
    
    # Démarrage du backend avec redémarrage automatique (bloquant)
    start_backend_with_restart
}

# Exécution
main "$@"

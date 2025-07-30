#!/bin/bash

# =============================================================================
# Script d'initialisation pour Stage-Chatbot-Polytech
# =============================================================================
# Ce script configure un serveur vierge pour faire fonctionner l'application
# Testé sur Ubuntu 20.04+ / Debian 11+

# pour pouvoir lancer le script faire:
# chmod +x init.sh
# ./init.sh

set -e  # Arrêter en cas d'erreur

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
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

# =============================================================================
# VÉRIFICATIONS PRÉLIMINAIRES
# =============================================================================

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Ce script ne doit PAS être exécuté en tant que root"
        log_info "Utilisez: ./init.sh"
        exit 1
    fi
}

check_config() {
    if [[ ! -f "config.env" ]]; then
        log_error "Fichier config.env introuvable"
        log_info "1. Copiez le template: cp config.template.env config.env"
        log_info "2. Éditez config.env avec vos valeurs"
        log_info "3. Relancez: ./init.sh"
        exit 1
    fi
    
    # Charger la configuration
    source config.env
    
    # Vérifier les variables critiques
    if [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == "your_openai_api_key_here" ]]; then
        log_error "OPENAI_API_KEY doit être configurée dans config.env"
        exit 1
    fi
    
    # Vérifier reCAPTCHA (optionnel mais recommandé)
    if [[ -z "$RECAPTCHA_SECRET_KEY" || "$RECAPTCHA_SECRET_KEY" == "your_recaptcha_secret_key_here" ]]; then
        log_warning "reCAPTCHA non configuré - fonctionnalité de sécurité désactivée"
        log_info "Pour activer reCAPTCHA, configurez RECAPTCHA_SECRET_KEY et RECAPTCHA_SITE_KEY"
    fi
    
    log_success "Configuration validée"
}

check_system() {
    log_info "Vérification du système..."
    
    # Vérifier l'OS
    if [[ ! -f /etc/debian_version ]] && [[ ! -f /etc/ubuntu-release ]]; then
        log_warning "Ce script est optimisé pour Debian/Ubuntu"
        read -p "Continuer quand même ? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Vérifier sudo
    if ! sudo -n true 2>/dev/null; then
        log_error "sudo est requis. Configurez sudo pour votre utilisateur."
        exit 1
    fi
    
    log_success "Système vérifié"
}

# =============================================================================
# INSTALLATION DES DÉPENDANCES SYSTÈME
# =============================================================================

install_system_deps() {
    log_info "Installation des dépendances système..."
    
    sudo apt update
    sudo apt install -y \
        python3.12 \
        python3.12-venv \
        python3.12-dev \
        python3-pip \
        nodejs \
        npm \
        nginx \
        curl \
        wget \
        git \
        build-essential \
        pkg-config \
        libssl-dev \
        libffi-dev \
        lsof \
        psmisc
    
    # Vérifier les versions
    python3.12 --version
    node --version
    npm --version
    nginx -v
    
    log_success "Dépendances système installées"
}

# =============================================================================
# CONFIGURATION PYTHON
# =============================================================================

setup_python_env() {
    log_info "Configuration de l'environnement Python..."
    
    # Créer l'environnement virtuel
    if [[ ! -d ".venv" ]]; then
        python3.12 -m venv .venv
        log_success "Environnement virtuel créé"
    fi
    
    # Activer l'environnement
    source .venv/bin/activate
    
    # Mettre à jour pip
    pip install --upgrade pip setuptools wheel
    
    # Installer les dépendances backend
    if [[ -f "Fastapi/backend/requirements.txt" ]]; then
        pip install -r Fastapi/backend/requirements.txt
        log_success "Dépendances Python installées"
    else
        log_warning "requirements.txt introuvable, installation manuelle nécessaire"
    fi
}

# =============================================================================
# CONFIGURATION FRONTEND
# =============================================================================

setup_frontend() {
    log_info "Configuration du frontend..."
    
    cd Fastapi/frontend
    
    # Installer les dépendances
    npm install
    
    # Build pour production si en mode production
    if [[ "$DEPLOYMENT_MODE" == "production" ]]; then
        npm run build
        log_success "Frontend buildé pour production"
    fi
    
    cd ../../
    log_success "Frontend configuré"
}

# =============================================================================
# GÉNÉRATION DES CERTIFICATS SSL
# =============================================================================

generate_ssl_certs() {
    log_info "Génération des certificats SSL..."
    
    mkdir -p ssl
    
    if [[ -z "$SSL_CERT_PATH" ]] || [[ -z "$SSL_KEY_PATH" ]]; then
        log_info "Génération de certificats auto-signés..."
        
        # Créer le fichier de config OpenSSL
        cat > ssl/openssl.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = ${SSL_COUNTRY}
ST = ${SSL_STATE}
L = ${SSL_CITY}
O = ${SSL_ORGANIZATION}
OU = ${SSL_UNIT}
CN = ${SERVER_DOMAIN}
emailAddress = ${SSL_EMAIL}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${SERVER_DOMAIN}
DNS.2 = localhost
IP.1 = ${SERVER_IP}
IP.2 = 127.0.0.1
EOF
        
        # Générer la clé privée et le certificat
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/polybot.key \
            -out ssl/polybot.crt \
            -config ssl/openssl.conf \
            -extensions v3_req
        
        SSL_CERT_PATH="$(pwd)/ssl/polybot.crt"
        SSL_KEY_PATH="$(pwd)/ssl/polybot.key"
        
        log_success "Certificats SSL générés"
    else
        log_info "Utilisation des certificats SSL existants"
    fi
}

# =============================================================================
# GÉNÉRATION DES FICHIERS .ENV
# =============================================================================

generate_env_files() {
    log_info "Génération des fichiers .env..."
    
    # Vérifier les clés reCAPTCHA
    if [[ -z "$RECAPTCHA_SECRET_KEY" || "$RECAPTCHA_SECRET_KEY" == "your_recaptcha_secret_key_here" ]]; then
        log_warning "RECAPTCHA_SECRET_KEY non configurée - reCAPTCHA désactivé"
        RECAPTCHA_SECRET_KEY=""
    fi
    
    if [[ -z "$RECAPTCHA_SITE_KEY" || "$RECAPTCHA_SITE_KEY" == "your_recaptcha_site_key_here" ]]; then
        log_warning "RECAPTCHA_SITE_KEY non configurée - reCAPTCHA désactivé"
        RECAPTCHA_SITE_KEY=""
    fi
    
    # .env simple pour new_filler (seulement l'essentiel)
    cat > Document_handler/new_filler/.env << EOF
# Configuration générée automatiquement par init.sh
OPENAI_API_KEY=${OPENAI_API_KEY}
EOF
    
    # .env pour le backend FastAPI
    cat > Fastapi/backend/.env << EOF
# Configuration générée automatiquement par init.sh
OPENAI_API_KEY=${OPENAI_API_KEY}
RECAPTCHA_SECRET_KEY=${RECAPTCHA_SECRET_KEY}
EOF
    
    # .env pour le frontend (garder /api comme vous l'avez configuré)
    cat > Fastapi/frontend/.env << EOF
# Configuration générée automatiquement par init.sh
VITE_BACKEND_URL=/api
VITE_RECAPTCHA_SITE_KEY=${RECAPTCHA_SITE_KEY}
EOF
    
    log_success "Fichiers .env générés"
}

# =============================================================================
# CONFIGURATION NGINX
# =============================================================================

setup_nginx() {
    log_info "Configuration de Nginx..."
    
    # Créer les répertoires de logs
    sudo mkdir -p /var/log/nginx/stage-chatbot
    
    # Vérifier si les fichiers de config nginx existent et les configurer
    if [[ -f "Fastapi/nginx/nginx-https.conf" ]]; then
        # Configuration HTTPS (seul port exposé à l'extérieur : 443)
        # Remplacer les placeholders dans la config HTTPS
        sed -i "s|SERVER_DOMAIN|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx-https.conf
        sed -i "s|BACKEND_PORT|${BACKEND_PORT}|g" Fastapi/nginx/nginx-https.conf
        sed -i "s|FRONTEND_PORT|${FRONTEND_PORT}|g" Fastapi/nginx/nginx-https.conf
        sed -i "s|SSL_CERT_PATH|${SSL_CERT_PATH}|g" Fastapi/nginx/nginx-https.conf
        sed -i "s|SSL_KEY_PATH|${SSL_KEY_PATH}|g" Fastapi/nginx/nginx-https.conf
        
        # Tester la configuration HTTPS
        sudo nginx -t -c "$(pwd)/Fastapi/nginx/nginx-https.conf"
        
        log_success "Configuration Nginx HTTPS prête (port 443 exposé, /api -> backend:${BACKEND_PORT})"
    else
        log_warning "Fichier nginx-https.conf introuvable"
    fi
    
    # Configuration HTTP de base (pour développement)
    if [[ -f "Fastapi/nginx/nginx.conf" ]]; then
        sed -i "s|SERVER_DOMAIN|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx.conf
        sed -i "s|BACKEND_PORT|${BACKEND_PORT}|g" Fastapi/nginx/nginx.conf
        sed -i "s|FRONTEND_PORT|${FRONTEND_PORT}|g" Fastapi/nginx/nginx.conf
        
        log_success "Configuration Nginx HTTP prête (développement)"
    fi
    
    log_success "Nginx configuré"
}

# =============================================================================
# CRÉATION DES RÉPERTOIRES ET PERMISSIONS
# =============================================================================

setup_directories() {
    log_info "Création des répertoires..."
    
    # Créer les répertoires nécessaires (paths relatifs depuis le projet)
    mkdir -p logs
    mkdir -p chroma_db
    mkdir -p Document_handler/Corpus/{data_sites,pdf_man,json_normalized,test}
    mkdir -p Document_handler/new_filler/{input_maps,vect_maps,output_maps,progress}
    
    # Permissions appropriées
    chmod 755 logs
    chmod 755 chroma_db
    
    log_success "Répertoires créés"
}

# =============================================================================
# CRÉATION DES SERVICES SYSTEMD (OPTIONNEL)
# =============================================================================

create_systemd_services() {
    if [[ "$DEPLOYMENT_MODE" == "production" ]]; then
        log_info "Création des services systemd..."
        
        # Service backend
        sudo tee /etc/systemd/system/stage-chatbot-backend.service > /dev/null << EOF
[Unit]
Description=Stage Chatbot Backend
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${WORK_DIR}
Environment=PATH=${WORK_DIR}/.venv/bin
ExecStart=${WORK_DIR}/.venv/bin/uvicorn Fastapi.backend.main:app --host 0.0.0.0 --port ${BACKEND_PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
        
        # Activer les services
        sudo systemctl daemon-reload
        sudo systemctl enable stage-chatbot-backend
        
        log_success "Services systemd créés"
    fi
}

# =============================================================================
# TESTS DE VÉRIFICATION
# =============================================================================

run_tests() {
    log_info "Exécution des tests de vérification..."
    
    # Test de l'environnement Python
    source .venv/bin/activate
    python3 -c "import fastapi, openai, chromadb; print('Modules Python OK')"
    
    # Test de la configuration OpenAI
    python3 -c "
import os
os.environ['OPENAI_API_KEY'] = '${OPENAI_API_KEY}'
import openai
client = openai.OpenAI()
print('Configuration OpenAI OK')
"
    
    log_success "Tests passés avec succès"
}

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

main() {
    log_info "🚀 Initialisation de Stage-Chatbot-Polytech"
    log_info "=============================================="
    
    # Vérifications
    check_root
    check_config
    check_system
    
    # Installation et configuration
    install_system_deps
    setup_python_env
    setup_frontend
    generate_ssl_certs
    generate_env_files
    setup_directories
    setup_nginx
    create_systemd_services
    
    # Tests
    run_tests
    
    log_success "🎉 Initialisation terminée avec succès !"
    echo
    log_info "=== DÉPLOIEMENT ET ACCÈS ==="
    log_info "Pour PRODUCTION (HTTPS, port 443 exposé, redémarrage auto):"
    log_info "  1. Démarrer: ./start-production.sh"
    log_info "  2. Accès: https://${SERVER_DOMAIN}:443"
    log_info "  3. API via: https://${SERVER_DOMAIN}/api/*"
    log_info "  4. Monitoring: ./monitor.sh"
    echo
    log_info "Pour DÉVELOPPEMENT (HTTPS dev):"
    log_info "  1. Démarrer: ./start-https.sh"
    log_info "  2. Accès: https://${SERVER_DOMAIN}:443"
    echo
    log_info "Pour DÉVELOPPEMENT (HTTP local):"
    log_info "  1. Démarrer: ./start.sh"  
    log_info "  2. Accès: http://${SERVER_DOMAIN}"
    echo
    log_info "=== FONCTIONNALITÉS PRODUCTION ==="
    log_info "- Frontend buildé et servi par Nginx"
    log_info "- Backend avec ${WORKERS:-2} workers"
    log_info "- Redémarrage automatique toutes les heures (cache)"
    log_info "- Logs rotatifs et monitoring intégré"
    log_info "- Arrêt propre avec Ctrl+C"
    echo
    log_info "=== CONFIGURATION ==="
    log_info "Fichiers .env générés:"
    log_info "- Document_handler/new_filler/.env (minimal)"
    log_info "- Fastapi/backend/.env (avec reCAPTCHA)"
    log_info "- Fastapi/frontend/.env (VITE_BACKEND_URL=/api)"
    echo
    if [[ -n "$RECAPTCHA_SECRET_KEY" && "$RECAPTCHA_SECRET_KEY" != "your_recaptcha_secret_key_here" ]]; then
        log_success "✅ reCAPTCHA configuré et activé"
    else
        log_warning "⚠️  reCAPTCHA non configuré - sécurité réduite"
    fi
}

# Exécution
main "$@"

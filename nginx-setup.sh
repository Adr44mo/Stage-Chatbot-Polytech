#!/bin/bash

# =============================================================================
# Script de configuration et test Nginx pour Stage-Chatbot-Polytech
# À lancer avec sudo si besoin
# =============================================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Charger la configuration
if [[ ! -f "config.env" ]]; then
    log_error "Fichier config.env introuvable. Placez-vous dans le dossier du projet."
    exit 1
fi
source config.env
PROJECT_PATH="$(pwd)"
FRONTEND_DIST_PATH="$PROJECT_PATH/Fastapi/frontend/dist"

setup_nginx() {
    log_info "Configuration de Nginx..."
    sudo mkdir -p /var/log/nginx/stage-chatbot
    log_info "Répertoires de logs nginx créés"
    if [[ "$DEPLOYMENT_MODE" == "production" ]] && [[ -f "Fastapi/nginx/nginx-production.conf" ]]; then
        log_info "Configuration Nginx pour PRODUCTION..."
        cp "Fastapi/nginx/nginx-production.conf" "Fastapi/nginx/nginx-production-configured.conf"
        sed -i "s|PROJECT_PATH|${PROJECT_PATH}|g" Fastapi/nginx/nginx-production-configured.conf
        sed -i "s|SERVER_DOMAIN|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx-production-configured.conf
        sed -i "s|SERVER_IP|${SERVER_IP}|g" Fastapi/nginx/nginx-production-configured.conf
        sed -i "s|BACKEND_PORT|${BACKEND_PORT}|g" Fastapi/nginx/nginx-production-configured.conf
        sed -i "s|SSL_CERT_PATH|${SSL_CERT_PATH}|g" Fastapi/nginx/nginx-production-configured.conf
        sed -i "s|SSL_KEY_PATH|${SSL_KEY_PATH}|g" Fastapi/nginx/nginx-production-configured.conf
        NGINX_OUTPUT=$(sudo nginx -t -c "$(pwd)/Fastapi/nginx/nginx-production-configured.conf" 2>&1)
        echo "$NGINX_OUTPUT" | grep -q 'ssl_stapling' && {
            log_warning "Nginx : warning ssl_stapling ignoré (certificat auto-signé ou intermédiaire manquant)"
            log_info "Ce warning est normal avec un certificat auto-signé et n'affecte pas le fonctionnement HTTPS."
        }
        if echo "$NGINX_OUTPUT" | grep -q 'syntax is ok' && echo "$NGINX_OUTPUT" | grep -q 'test is successful'; then
            log_success "Configuration Nginx PRODUCTION prête (frontend buildé + backend:${BACKEND_PORT})"
        else
            log_error "Configuration Nginx PRODUCTION invalide"
            echo "$NGINX_OUTPUT"
            return 1
        fi
    elif [[ -f "Fastapi/nginx/nginx-https.conf" ]]; then
        log_info "Configuration Nginx pour DÉVELOPPEMENT..."
        cp "Fastapi/nginx/nginx-https.conf" "Fastapi/nginx/nginx-https-configured.conf"
        sed -i "s|/srv/partage/Stage-Chatbot-Polytech|${PROJECT_PATH}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|134\.157\.105\.72|${SERVER_IP}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|polybot|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|SERVER_DOMAIN|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|BACKEND_PORT|${BACKEND_PORT}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|FRONTEND_PORT|${FRONTEND_PORT}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|SSL_CERT_PATH|${SSL_CERT_PATH}|g" Fastapi/nginx/nginx-https-configured.conf
        sed -i "s|SSL_KEY_PATH|${SSL_KEY_PATH}|g" Fastapi/nginx/nginx-https-configured.conf
        if sudo nginx -t -c "$(pwd)/Fastapi/nginx/nginx-https-configured.conf"; then
            log_success "Configuration Nginx DÉVELOPPEMENT prête (port 443 exposé, /api -> backend:${BACKEND_PORT})"
        else
            log_error "Configuration Nginx DÉVELOPPEMENT invalide"
            return 1
        fi
    else
        log_error "Aucun fichier de configuration Nginx trouvé"
        return 1
    fi
    if [[ -f "Fastapi/nginx/nginx.conf" ]]; then
        log_info "Configuration Nginx HTTP (développement local)..."
        cp "Fastapi/nginx/nginx.conf" "Fastapi/nginx/nginx-configured.conf"
        sed -i "s|134\.157\.105\.72|${SERVER_IP}|g" Fastapi/nginx/nginx-configured.conf
        sed -i "s|polybot|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx-configured.conf
        sed -i "s|SERVER_DOMAIN|${SERVER_DOMAIN}|g" Fastapi/nginx/nginx-configured.conf
        sed -i "s|BACKEND_PORT|${BACKEND_PORT}|g" Fastapi/nginx/nginx-configured.conf
        sed -i "s|FRONTEND_PORT|${FRONTEND_PORT}|g" Fastapi/nginx/nginx-configured.conf
        log_success "Configuration Nginx HTTP prête (développement local)"
    fi
    log_success "Nginx configuré selon DEPLOYMENT_MODE=${DEPLOYMENT_MODE}"
}

setup_nginx

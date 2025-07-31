#!/bin/bash

# Script d'installation et de lancement complet pour Stage-Chatbot-Polytech

set -e

echo "==> Mise en exécution des scripts"
chmod +x init.sh
chmod +x nginx-setup.sh
chmod +x start-production.sh
chmod +x start-development.sh
chmod +x stop-production.sh

echo "==> Initialisation de l'application (sans sudo)"
./init.sh

echo "==> Configuration de Nginx (avec sudo)"
sudo ./nginx-setup.sh

MODE=$(grep '^DEPLOYMENT_MODE=' config.env | cut -d'=' -f2)
if [[ "$MODE" == "production" ]]; then
    echo "==> Installation terminée : MODE PRODUCTION"
    echo "Accès : https://$SERVER_DOMAIN:443 (Nginx, backend, frontend buildé)"
    echo "==> Vous pouvez lancer la production (avec ./start-production.sh)"
else
    echo "==> Installation terminée : MODE DÉVELOPPEMENT"
    echo "Accès : https://$SERVER_DOMAIN:443 (Nginx, hot reload, dev server)"
    echo "==> Vous pouvez lancer le développement (avec ./start-development.sh)"
fi

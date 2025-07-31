#!/bin/bash

# Script d'installation et de lancement complet pour Stage-Chatbot-Polytech

set -e

echo "==> Mise en exécution des scripts"
chmod +x init.sh
chmod +x Fastapi/nginx/nginx-setup.sh
chmod +x start-production.sh

echo "==> Initialisation de l'application (sans sudo)"
./init.sh

echo "==> Configuration de Nginx (avec sudo)"
sudo Fastapi/nginx/nginx-setup.sh

echo "==> Fin de l'installation"

echo "==> Vous pouvez lancer la production (avec ./start-production.sh)"
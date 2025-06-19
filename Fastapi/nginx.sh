#!/bin/bash

# Déplace ton fichier
sudo cp Fastapi/nginx/nginx.conf /etc/nginx/sites-available/stage-chatbot

# Active la conf
sudo ln -s /etc/nginx/sites-available/stage-chatbot /etc/nginx/sites-enabled/

# Teste que tout est bon
sudo nginx -t

# Recharge
sudo systemctl reload nginx
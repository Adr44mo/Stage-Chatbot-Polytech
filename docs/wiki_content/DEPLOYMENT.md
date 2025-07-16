# 🚀 Guide de Déploiement

Ce guide détaille les différentes méthodes de déploiement du système RAG Polytech, de l'environnement de développement à la production.

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Déploiement Local](#déploiement-local)
3. [Déploiement avec Docker](#déploiement-avec-docker)
4. [Déploiement Production](#déploiement-production)
5. [Configuration Nginx](#configuration-nginx)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

## 🔧 Prérequis

### Système
- **OS** : Linux (Ubuntu 20.04+), macOS, Windows 10+
- **RAM** : 4GB minimum, 8GB recommandé
- **Stockage** : 10GB minimum, 20GB recommandé
- **Processeur** : 2 cores minimum, 4 cores recommandé

### Logiciels
- **Python** : 3.12+
- **Node.js** : 18+
- **Redis** : 6+ (optionnel)
- **Nginx** : 1.18+ (production)
- **Docker** : 20+ (optionnel)

## 🏠 Déploiement Local

### 1. Clonage et Installation

```bash
# 1. Cloner le repository
git clone https://github.com/username/Stage-Chatbot-Polytech.git
cd Stage-Chatbot-Polytech

# 2. Configuration environnement
cp .env.example .env
nano .env  # Éditer avec vos valeurs
```

### 2. Configuration Backend

```bash
# Installer les dépendances Python
cd Fastapi/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Initialiser la base de données
python -c "from app.auth.database import create_db_and_tables; create_db_and_tables()"

# Vectoriser les documents
python -m Document_handler.new_filler.main
```

### 3. Configuration Frontend

```bash
# Installer les dépendances Node.js
cd ../../Fastapi/frontend
npm install

# Configuration environnement
cp .env.local.example .env.local
nano .env.local  # Éditer avec vos valeurs
```

### 4. Démarrage

```bash
# Option A : Script automatique
cd ../../
chmod +x start.sh
./start.sh

# Option B : Manuel
# Terminal 1 : Backend
cd Fastapi/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 : Frontend
cd Fastapi/frontend
npm run dev
```

### 5. Vérification

```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:5173

# Test API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Bonjour", "chat_history": []}'
```

## 🐳 Déploiement avec Docker

### 1. Dockerfile Backend

```dockerfile
# Fastapi/backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Variables d'environnement
ENV PYTHONPATH="/app"
ENV PORT=8000

# Exposer le port
EXPOSE $PORT

# Santé check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Dockerfile Frontend

```dockerfile
# Fastapi/frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copier package.json et installer les dépendances
COPY package*.json ./
RUN npm ci --only=production

# Copier le code et builder
COPY . .
RUN npm run build

# Stage de production
FROM nginx:alpine

# Copier les fichiers buildés
COPY --from=builder /app/dist /usr/share/nginx/html

# Configuration nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Exposer le port
EXPOSE 80

# Commande de démarrage
CMD ["nginx", "-g", "daemon off;"]
```

### 3. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: 
      context: ./Fastapi/backend
      dockerfile: Dockerfile
    container_name: polytech-backend
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - USE_INTELLIGENT_RAG=true
      - DATABASE_URL=sqlite:///./logs/rag_system.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./logs:/app/logs
      - ./Document_handler:/app/Document_handler
    ports:
      - "8000:8000"
    depends_on:
      - redis
    restart: unless-stopped

  frontend:
    build: 
      context: ./Fastapi/frontend
      dockerfile: Dockerfile
    container_name: polytech-frontend
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: polytech-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 4. Démarrage Docker

```bash
# Construire et démarrer
docker-compose up -d --build

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down

# Nettoyer
docker-compose down -v
docker system prune -a
```

## 🏭 Déploiement Production

### 1. Configuration Serveur

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installer les dépendances
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm nginx redis-server

# Créer utilisateur dédié
sudo useradd -m -s /bin/bash polytech
sudo usermod -aG sudo polytech

# Configurer les permissions
sudo chown -R polytech:polytech /var/www/
```

### 2. Configuration Application

```bash
# Cloner en production
sudo -u polytech git clone https://github.com/username/Stage-Chatbot-Polytech.git /var/www/polytech-chatbot
cd /var/www/polytech-chatbot

# Configuration environnement
sudo -u polytech cp .env.example .env
sudo -u polytech nano .env

# Variables production
export ENVIRONMENT=production
export DEBUG=false
export USE_INTELLIGENT_RAG=true
export OPENAI_API_KEY=your_production_key
export SECRET_KEY=your_production_secret
```

### 3. Installation Backend

```bash
# Environnement Python
sudo -u polytech python3.12 -m venv /var/www/polytech-chatbot/venv
source /var/www/polytech-chatbot/venv/bin/activate
pip install -r Fastapi/backend/requirements.txt

# Initialisation base de données
cd Fastapi/backend
python -c "from app.auth.database import create_db_and_tables; create_db_and_tables()"

# Vectorisation documents
python -m Document_handler.new_filler.main
```

### 4. Installation Frontend

```bash
# Build frontend
cd ../../Fastapi/frontend
sudo -u polytech npm install
sudo -u polytech npm run build

# Copier vers nginx
sudo cp -r dist/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

### 5. Configuration Systemd

```ini
# /etc/systemd/system/polytech-backend.service
[Unit]
Description=Polytech Chatbot Backend
After=network.target

[Service]
Type=simple
User=polytech
Group=polytech
WorkingDirectory=/var/www/polytech-chatbot/Fastapi/backend
Environment=PATH=/var/www/polytech-chatbot/venv/bin
ExecStart=/var/www/polytech-chatbot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable polytech-backend
sudo systemctl start polytech-backend

# Vérifier
sudo systemctl status polytech-backend
```

## 🌐 Configuration Nginx

### 1. Configuration Site

```nginx
# /etc/nginx/sites-available/polytech-chatbot
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend (React)
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffers
        proxy_buffer_size 4k;
        proxy_buffers 4 32k;
        proxy_busy_buffers_size 64k;
    }
    
    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### 2. Activation et SSL

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/polytech-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL avec Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Renouvellement automatique
sudo crontab -e
# Ajouter : 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring & Maintenance

### 1. Monitoring Basique

```bash
# Script de monitoring
#!/bin/bash
# /usr/local/bin/polytech-monitor.sh

# Vérifier le backend
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend down - restarting..."
    sudo systemctl restart polytech-backend
fi

# Vérifier nginx
if ! systemctl is-active --quiet nginx; then
    echo "Nginx down - restarting..."
    sudo systemctl restart nginx
fi

# Vérifier l'espace disque
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage high: ${DISK_USAGE}%"
    # Nettoyer les logs
    sudo journalctl --vacuum-time=7d
fi
```

### 2. Cron Jobs

```bash
# Crontab pour maintenance
sudo crontab -e

# Monitoring toutes les 5 minutes
*/5 * * * * /usr/local/bin/polytech-monitor.sh

# Backup quotidien
0 2 * * * /usr/local/bin/backup-polytech.sh

# Nettoyage logs hebdomadaire
0 3 * * 0 /usr/local/bin/cleanup-logs.sh

# Mise à jour des documents
0 4 * * * cd /var/www/polytech-chatbot && python -m Document_handler.new_filler.main
```

### 3. Backup Script

```bash
#!/bin/bash
# /usr/local/bin/backup-polytech.sh

BACKUP_DIR="/var/backups/polytech"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup base de données
cp /var/www/polytech-chatbot/logs/rag_system.db $BACKUP_DIR/rag_system_$DATE.db

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /var/www/polytech-chatbot/.env

# Nettoyer les anciens backups (> 30 jours)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

## 🔧 Troubleshooting

### Problèmes Courants

#### 1. Backend ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u polytech-backend -f

# Vérifier la configuration
cd /var/www/polytech-chatbot/Fastapi/backend
source /var/www/polytech-chatbot/venv/bin/activate
python -c "from main import app; print('Config OK')"

# Vérifier les dépendances
pip check
```

#### 2. Frontend ne se charge pas
```bash
# Vérifier nginx
sudo nginx -t
sudo systemctl status nginx

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/html/
```

#### 3. Problèmes de base de données
```bash
# Vérifier la base
cd /var/www/polytech-chatbot/Fastapi/backend
python -c "from app.auth.database import engine; print(engine.execute('SELECT 1').fetchone())"

# Recréer si nécessaire
python -c "from app.auth.database import create_db_and_tables; create_db_and_tables()"
```

#### 4. Problèmes OpenAI
```bash
# Tester la clé API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### Logs Utiles

```bash
# Logs backend
sudo journalctl -u polytech-backend -f

# Logs nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs système
sudo tail -f /var/log/syslog

# Logs application
tail -f /var/www/polytech-chatbot/logs/system.log
```

### Performance

```bash
# Surveiller les ressources
htop
free -h
df -h

# Surveiller les processus
ps aux | grep uvicorn
ps aux | grep nginx

# Surveiller les connexions
netstat -tulpn | grep :8000
netstat -tulpn | grep :80
```

## 🔄 Mise à Jour

### Processus de Mise à Jour

```bash
# 1. Backup
/usr/local/bin/backup-polytech.sh

# 2. Arrêter les services
sudo systemctl stop polytech-backend
sudo systemctl stop nginx

# 3. Mettre à jour le code
cd /var/www/polytech-chatbot
sudo -u polytech git pull origin main

# 4. Mettre à jour les dépendances
source venv/bin/activate
pip install -r Fastapi/backend/requirements.txt

cd Fastapi/frontend
npm install
npm run build

# 5. Migrer si nécessaire
# python migrate.py

# 6. Redémarrer
sudo systemctl start polytech-backend
sudo systemctl start nginx

# 7. Vérifier
curl http://localhost:8000/health
```

---

Ce guide couvre les aspects essentiels du déploiement. Pour des besoins spécifiques, n'hésitez pas à adapter les configurations selon votre environnement.

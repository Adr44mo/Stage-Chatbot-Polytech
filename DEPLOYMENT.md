# Déploiement Stage-Chatbot-Polytech

Guide de déploiement sur serveur vierge.

## Installation Rapide

### 1. Clone du projet
```bash
git clone https://github.com/your-repo/Stage-Chatbot-Polytech.git
cd Stage-Chatbot-Polytech
```

### 2. Configuration
```bash
# Copier le template de configuration
cp config.template.env config.env

# Éditer avec vos valeurs
nano config.env
```

**Variables obligatoires :**
- `OPENAI_API_KEY` : Votre clé API OpenAI
- `RECAPTCHA_SECRET_KEY` et `RECAPTCHA_SITE_KEY` : Clés reCAPTCHA (recommandé)
- `SERVER_DOMAIN` : Domaine ou IP de votre serveur

**Variables optionnelles (production) :**
- `WORKERS` : Nombre de workers uvicorn (défaut: 2)
- `RESTART_INTERVAL` : Intervalle de redémarrage en secondes (défaut: 3600 = 1h)

### 3. Initialisation
```bash
# Rendre le script exécutable
chmod +x init.sh

# Lancer l'initialisation (sans sudo)
./init.sh
```

Le script va :
- Installer toutes les dépendances système
- Configurer Python et Node.js
- Générer les certificats SSL
- Créer les fichiers .env
- Configurer Nginx

### 4. Démarrage

**Pour PRODUCTION (optimisé, redémarrage automatique) :**
Ouvrez le fichier `start-production.sh` pour modifier le chemin du dossier du projet :

```bash
nano start-production.sh
```

Dans ce fichier, repérez la ligne contenant :

```bash
PROJECT_ROOT="/srv/partage/Stage-Chatbot-Polytech"
```

Remplacez le chemin par l'emplacement réel de votre dossier de projet. Par exemple, si votre projet est dans `/home/votre-utilisateur/mon-projet`, modifiez la ligne ainsi :

```bash
PROJECT_ROOT="/home/votre-utilisateur/Stage-Chatbot-Polytech"
```

Enregistrez le fichier et quittez l'éditeur.  
Cette modification est nécessaire pour que le script fonctionne correctement lors du lancement en production.

```bash
./start-production.sh
```

**Pour DÉVELOPPEMENT (HTTPS) :**
```bash
./start-https.sh
```

**Pour DÉVELOPPEMENT (HTTP local) :**
```bash
./start.sh
```

## Scripts de démarrage

### Mode Production (`./start-production.sh`)
- **Optimisé pour production** avec build frontend statique
- **Multi-workers** uvicorn (configuré via `WORKERS`)
- **Redémarrage automatique** toutes les heures pour vider le cache
- **Logs rotatifs** avec archivage automatique
- **Monitoring intégré** avec script `./monitor.sh`
- **Arrêt propre** avec Ctrl+C
- **Port 443 uniquement** exposé à l'extérieur

### Mode Développement HTTPS (`./start-https.sh`)
- **HTTPS avec certificats auto-signés**
- **Frontend en mode dev** avec hot-reload
- **Backend avec --reload** pour développement
- **Port 443 exposé** pour tests HTTPS

### Mode Développement HTTP (`./start.sh`)
- **HTTP simple** pour développement local
- **Tous les ports exposés** (80, 8000, 5173)
- **Hot-reload** frontend et backend

## Architecture de déploiement

### Ports et accès
- **Port 443** : Seul port exposé à l'extérieur (HTTPS)
- **Port 8000** : Backend FastAPI (interne)
- **Port 5173** : Frontend Vite (interne)

### Routing Nginx
```
https://votre-domaine:443/        → Frontend (mode prod: fichiers statiques, mode dev: port 5173)
https://votre-domaine:443/api/*   → Backend (port 8000)
```

### Fonctionnalités Production
- **Frontend buildé** servi directement par Nginx (plus rapide)
- **Multi-workers** backend pour gérer plus de connexions simultanées
- **Redémarrage automatique** pour éviter l'accumulation en cache/mémoire
- **Logs structurés** avec timestamps et rotation automatique
- **Monitoring en temps réel** via `./monitor.sh`
- **Gestion propre des signaux** pour arrêt sans corruption

### Fichiers .env générés

**`Document_handler/new_filler/.env`** (minimal) :
```env
OPENAI_API_KEY=your_key
```

**`Fastapi/backend/.env`** :
```env
OPENAI_API_KEY=your_key
RECAPTCHA_SECRET_KEY=your_secret
```

**`Fastapi/frontend/.env`** :
```env
VITE_BACKEND_URL=/api
VITE_RECAPTCHA_SITE_KEY=your_site_key
```

## Monitoring et Maintenance

### Surveillance en temps réel
```bash
# Status général des services
./monitor.sh

# Logs en temps réel
tail -f logs/backend.log
tail -f logs/frontend.log

# Vérifier les processus
ps aux | grep uvicorn
ps aux | grep nginx
```

### Commandes utiles Production
```bash
# Redémarrer uniquement le backend (sans arrêter nginx)
kill -TERM $(cat app.pid)

# Vérifier l'espace disque et performances
df -h
free -h
htop

# Analyser les connexions
ss -tuln | grep 443
netstat -an | grep ESTABLISHED | wc -l
```

### Configuration reCAPTCHA

1. Aller sur [Google reCAPTCHA](https://www.google.com/recaptcha/admin)
2. Créer un site reCAPTCHA v2
3. Ajouter votre domaine aux domaines autorisés
4. Copier les clés dans `config.env`

## Sécurité

- Certificats SSL auto-signés générés automatiquement
- reCAPTCHA pour protection anti-spam
- CORS configuré pour votre domaine
- Seul le port 443 exposé

## Troubleshooting

### Erreur de permissions
```bash
sudo chown -R $USER:$USER /srv/partage/Stage-Chatbot-Polytech
```

### Nginx ne démarre pas
```bash
sudo nginx -t -c /path/to/nginx-https.conf
sudo systemctl status nginx
```

### Certificats SSL invalides
```bash
rm -rf ssl/
./init.sh  # Régénère les certificats
```

### Port déjà utilisé
```bash
sudo pkill -f nginx
sudo pkill -f uvicorn
sudo pkill -f vite
./start-production.sh  # ou start-https.sh pour dev
```

### Backend ne redémarre pas automatiquement
```bash
# Vérifier le fichier PID
ls -la app.pid

# Vérifier les logs
tail -20 logs/backend.log

# Redémarrage manuel
kill $(cat app.pid) 2>/dev/null || true
./start-production.sh
```

### Performance dégradée
```bash
# Vérifier l'utilisation mémoire
./monitor.sh

# Nettoyer les logs volumineux
find logs/ -name "*.log" -size +50M -exec mv {} {}.old \;

# Ajuster l'intervalle de redémarrage (config.env)
RESTART_INTERVAL=1800  # 30 minutes au lieu d'1 heure
```

## Support

En cas de problème :
1. **Vérifier le monitoring** : `./monitor.sh`
2. **Consulter les logs** : `tail -f logs/backend.log`
3. **Tester nginx** : `sudo nginx -t`
4. **Vérifier la config** : `cat config.env`

### Logs importants
- **Application** : `./logs/backend.log`, `./logs/frontend.log`
- **Nginx** : `/var/log/nginx/`
- **Système** : `/var/log/syslog`

### Scripts utiles
- **Démarrage production** : `./start-production.sh`
- **Monitoring** : `./monitor.sh`
- **Initialisation** : `./init.sh`
- **Configuration** : `config.env`

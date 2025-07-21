"""
Routes API pour la gestion des tâches automatiques et du nettoyage
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from datetime import datetime
from .automated_tasks import AutomatedMaintenanceService
from color_utils import ColorPrint

cp = ColorPrint()

router = APIRouter(prefix="/intelligent-rag/maintenance", tags=["Maintenance"])

# Instance globale du service de maintenance
maintenance_service = AutomatedMaintenanceService()

@router.get("/status")
def get_maintenance_status():
    """Obtenir le statut du service de maintenance automatique"""
    return {
        "service_running": maintenance_service.running,
        "next_scheduled_tasks": maintenance_service.get_next_scheduled_tasks(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/cleanup/manual")
def run_manual_cleanup(days_to_keep: int = Query(90, description="Nombre de jours de données à conserver")):
    """Déclencher un nettoyage manuel immédiat"""
    if days_to_keep < 1:
        raise HTTPException(status_code=400, detail="days_to_keep doit être supérieur à 0")
    
    if days_to_keep < 30:
        raise HTTPException(status_code=400, detail="Par sécurité, minimum 30 jours de données doivent être conservées")
    
    try:
        result = maintenance_service.run_manual_cleanup_now(days_to_keep)
        return {
            "message": f"Nettoyage manuel terminé (conservé {days_to_keep} jours)",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        cp.print_error(f"Erreur nettoyage manuel: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du nettoyage: {str(e)}")

@router.post("/service/start")
def start_maintenance_service():
    """Démarrer le service de maintenance automatique"""
    try:
        maintenance_service.start_background_service()
        return {
            "message": "Service de maintenance démarré",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        cp.print_error(f"Erreur démarrage service: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du démarrage: {str(e)}")

@router.post("/service/stop")
def stop_maintenance_service():
    """Arrêter le service de maintenance automatique"""
    try:
        maintenance_service.stop_background_service()
        return {
            "message": "Service de maintenance arrêté",
            "status": "stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        cp.print_error(f"Erreur arrêt service: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'arrêt: {str(e)}")

@router.get("/schedule")
def get_maintenance_schedule():
    """Obtenir le planning des tâches de maintenance"""
    return {
        "daily_maintenance": {
            "description": "Mise à jour des statistiques",
            "schedule": "Tous les jours à 02:00"
        },
        "weekly_cleanup": {
            "description": "Suppression des données de plus de 90 jours",
            "schedule": "Tous les dimanches à 03:00"
        },
        "monthly_cleanup": {
            "description": "Suppression des données de plus de 180 jours et stats de plus de 2 ans",
            "schedule": "Le 1er de chaque mois à 04:00"
        },
        "next_tasks": maintenance_service.get_next_scheduled_tasks(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/history")
def get_cleanup_history():
    """Obtenir un résumé des derniers nettoyages (placeholder)"""
    # Cette fonction pourrait être étendue pour stocker un historique des nettoyages
    return {
        "message": "Historique des nettoyages non encore implémenté",
        "suggestion": "Consultez les logs de l'application pour voir l'historique",
        "timestamp": datetime.utcnow().isoformat()
    }

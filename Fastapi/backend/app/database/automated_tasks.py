"""
Service complet de gestion automatique des données RAG
Inclut le nettoyage automatique, les statistiques et les tâches planifiées
"""

import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from typing import Dict, Any, List
from .database import get_session, engine
from .models import RAGConversation, RAGDailyStats, RAGMonthlyStats, RAGYearlyStats
from .models import Conversation, Message, RAGTokenOperation, RAGContextDocument
from .stats_manager import StatsManager
from color_utils import ColorPrint

cp = ColorPrint()

class AutomatedMaintenanceService:
    """Service unifié de maintenance automatique"""
    
    def __init__(self):
        self.stats_manager = StatsManager()
        self.running = False
        self.thread = None
    
    # ========================================
    # GESTION DES STATISTIQUES
    # ========================================
    
    async def update_daily_stats(self, date: datetime = None):
        """Mettre à jour les statistiques journalières"""
        if not date:
            date = datetime.now().date()
        
        try:
            with Session(engine) as session:
                daily_stats = await self.stats_manager.calculate_daily_stats(date, session)
                
                existing = session.exec(
                    select(RAGDailyStats).where(RAGDailyStats.date == date)
                ).first()
                
                if existing:
                    for key, value in daily_stats.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    new_stats = RAGDailyStats(date=date, **daily_stats)
                    session.add(new_stats)
                
                session.commit()
                cp.print_success(f"[Maintenance] Statistiques journalières mises à jour pour {date}")
                
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur mise à jour stats journalières: {e}")
    
    async def update_monthly_stats(self, year: int = None, month: int = None):
        """Mettre à jour les statistiques mensuelles"""
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        try:
            with Session(engine) as session:
                monthly_stats = await self.stats_manager.calculate_monthly_stats(year, month, session)
                
                existing = session.exec(
                    select(RAGMonthlyStats).where(
                        RAGMonthlyStats.year == year,
                        RAGMonthlyStats.month == month
                    )
                ).first()
                
                if existing:
                    for key, value in monthly_stats.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    new_stats = RAGMonthlyStats(year=year, month=month, **monthly_stats)
                    session.add(new_stats)
                
                session.commit()
                cp.print_success(f"[Maintenance] Statistiques mensuelles mises à jour pour {month}/{year}")
                
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur mise à jour stats mensuelles: {e}")
    
    async def update_yearly_stats(self, year: int = None):
        """Mettre à jour les statistiques annuelles"""
        if not year:
            year = datetime.now().year
        
        try:
            with Session(engine) as session:
                yearly_stats = await self.stats_manager.calculate_yearly_stats(year, session)
                
                existing = session.exec(
                    select(RAGYearlyStats).where(RAGYearlyStats.year == year)
                ).first()
                
                if existing:
                    for key, value in yearly_stats.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    new_stats = RAGYearlyStats(year=year, **yearly_stats)
                    session.add(new_stats)
                
                session.commit()
                cp.print_success(f"[Maintenance] Statistiques annuelles mises à jour pour {year}")
                
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur mise à jour stats annuelles: {e}")
    
    # ========================================
    # NETTOYAGE DES DONNÉES
    # ========================================
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Supprimer les données anciennes (conversations, messages, RAG) de plus de X jours"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with Session(engine) as session:
                # Compter les données avant suppression
                old_conversations = session.exec(
                    select(func.count(Conversation.id)).where(Conversation.created_at < cutoff_date)
                ).one()
                
                old_messages = session.exec(
                    select(func.count(Message.id)).where(Message.timestamp < cutoff_date)
                ).one()
                
                old_rag_conversations = session.exec(
                    select(func.count(RAGConversation.id)).where(RAGConversation.timestamp < cutoff_date)
                ).one()
                
                cp.print_info(f"[Maintenance] Nettoyage des données de plus de {days_to_keep} jours...")
                cp.print_info(f"[Maintenance] À supprimer: {old_conversations} conversations, {old_messages} messages, {old_rag_conversations} RAG conversations")
                
                # Supprimer les données liées aux RAG Conversations
                old_rag_ids = session.exec(
                    select(RAGConversation.id).where(RAGConversation.timestamp < cutoff_date)
                ).all()
                
                deleted_context_docs = 0
                deleted_token_ops = 0
                
                if old_rag_ids:
                    # Supprimer les documents contextuels et opérations de tokens
                    for rag_id in old_rag_ids:
                        context_docs = session.exec(
                            select(RAGContextDocument).where(RAGContextDocument.rag_conversation_id == rag_id)
                        ).all()
                        for doc in context_docs:
                            session.delete(doc)
                            deleted_context_docs += 1
                        
                        token_ops = session.exec(
                            select(RAGTokenOperation).where(RAGTokenOperation.rag_conversation_id == rag_id)
                        ).all()
                        for op in token_ops:
                            session.delete(op)
                            deleted_token_ops += 1
                
                # Supprimer les conversations principales
                for old_id in old_rag_ids:
                    rag_conv = session.get(RAGConversation, old_id)
                    if rag_conv:
                        session.delete(rag_conv)
                
                old_msgs = session.exec(
                    select(Message).where(Message.timestamp < cutoff_date)
                ).all()
                for msg in old_msgs:
                    session.delete(msg)
                
                old_convs = session.exec(
                    select(Conversation).where(Conversation.created_at < cutoff_date)
                ).all()
                for conv in old_convs:
                    session.delete(conv)
                
                session.commit()
                
                cp.print_success(f"[Maintenance] Nettoyage terminé: supprimé {old_conversations} conversations, {old_messages} messages, {old_rag_conversations} RAG conversations")
                cp.print_info(f"[Maintenance] Également supprimé: {deleted_context_docs} documents contextuels, {deleted_token_ops} opérations de tokens")
                
                return {
                    "deleted_conversations": old_conversations,
                    "deleted_messages": old_messages,
                    "deleted_rag_conversations": old_rag_conversations,
                    "deleted_context_docs": deleted_context_docs,
                    "deleted_token_ops": deleted_token_ops,
                    "cutoff_date": cutoff_date.isoformat(),
                    "days_kept": days_to_keep
                }
                
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur lors du nettoyage: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_stats(self, days_to_keep: int = 365):
        """Supprimer les anciennes statistiques journalières"""
        cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
        
        try:
            with Session(engine) as session:
                old_daily_stats = session.exec(
                    select(func.count(RAGDailyStats.id)).where(RAGDailyStats.date < cutoff_date)
                ).one()
                
                if old_daily_stats > 0:
                    old_stats = session.exec(
                        select(RAGDailyStats).where(RAGDailyStats.date < cutoff_date)
                    ).all()
                    for stat in old_stats:
                        session.delete(stat)
                    
                    session.commit()
                    cp.print_success(f"[Maintenance] Supprimé {old_daily_stats} statistiques journalières anciennes")
                    return {"deleted_daily_stats": old_daily_stats}
                else:
                    cp.print_info("[Maintenance] Aucune statistique ancienne à supprimer")
                    return {"deleted_daily_stats": 0}
                
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur lors du nettoyage des stats: {e}")
            return {"error": str(e)}
    
    # ========================================
    # TÂCHES DE MAINTENANCE
    # ========================================
    
    async def run_daily_maintenance(self):
        """Maintenance quotidienne"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        await self.update_daily_stats(yesterday)
        await self.update_monthly_stats()
        await self.update_yearly_stats()
        
        cp.print_success("[Maintenance] Maintenance quotidienne terminée")
    
    async def run_weekly_maintenance(self):
        """Maintenance hebdomadaire"""
        cp.print_info("[Maintenance] Début de la maintenance hebdomadaire...")
        
        cleanup_result = await self.cleanup_old_data(days_to_keep=90)
        stats_cleanup = await self.cleanup_old_stats(days_to_keep=365)
        
        cp.print_success("[Maintenance] Maintenance hebdomadaire terminée")
        return {
            "data_cleanup": cleanup_result,
            "stats_cleanup": stats_cleanup,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_manual_cleanup(self, days_to_keep: int = 90):
        """Nettoyage manuel avec nombre de jours personnalisé"""
        cp.print_info(f"[Maintenance] Nettoyage manuel: garder {days_to_keep} jours")
        return await self.cleanup_old_data(days_to_keep=days_to_keep)
    
    # ========================================
    # SERVICE EN ARRIÈRE-PLAN
    # ========================================
    
    def start_background_service(self):
        """Démarrer le service de tâches automatiques"""
        if self.running:
            cp.print_warning("[Maintenance] Service déjà en cours d'exécution")
            return
            
        self.running = True
        self._schedule_tasks()
        
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        cp.print_success("[Maintenance] Service de tâches automatiques démarré")
    
    def stop_background_service(self):
        """Arrêter le service de tâches automatiques"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        cp.print_info("[Maintenance] Service de tâches automatiques arrêté")
    
    def _schedule_tasks(self):
        """Planifier toutes les tâches automatiques"""
        schedule.every().day.at("02:00").do(self._run_daily_maintenance)
        schedule.every().sunday.at("03:00").do(self._run_weekly_cleanup)
        schedule.every().day.at("04:00").do(self._run_monthly_cleanup_check)
        
        cp.print_info("[Maintenance] Tâches planifiées:")
        cp.print_info("  - Maintenance quotidienne: tous les jours à 02:00")
        cp.print_info("  - Nettoyage hebdomadaire: tous les dimanches à 03:00")
        cp.print_info("  - Nettoyage mensuel: le 1er de chaque mois à 04:00")
    
    def _run_scheduler(self):
        """Boucle principale du planificateur"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                cp.print_error(f"[Maintenance] Erreur dans le planificateur: {e}")
                time.sleep(300)
    
    def _run_daily_maintenance(self):
        """Exécuter la maintenance quotidienne"""
        try:
            cp.print_info("[Maintenance] Début de la maintenance quotidienne...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_daily_maintenance())
            loop.close()
            cp.print_success("[Maintenance] Maintenance quotidienne terminée")
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur maintenance quotidienne: {e}")
    
    def _run_weekly_cleanup(self):
        """Exécuter le nettoyage hebdomadaire"""
        try:
            cp.print_info("[Maintenance] Début du nettoyage hebdomadaire...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_weekly_maintenance())
            loop.close()
            cp.print_success("[Maintenance] Nettoyage hebdomadaire terminé")
            cp.print_info(f"[Maintenance] Résultat: {result}")
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur nettoyage hebdomadaire: {e}")
    
    def _run_monthly_cleanup_check(self):
        """Vérifier si c'est le 1er du mois pour le nettoyage mensuel"""
        today = datetime.now()
        if today.day == 1:
            self._run_monthly_cleanup()
    
    def _run_monthly_cleanup(self):
        """Exécuter le nettoyage mensuel des très anciennes données"""
        try:
            cp.print_info("[Maintenance] Début du nettoyage mensuel...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.cleanup_old_data(days_to_keep=180))
            stats_result = loop.run_until_complete(self.cleanup_old_stats(days_to_keep=730))
            
            loop.close()
            cp.print_success("[Maintenance] Nettoyage mensuel terminé")
            cp.print_info(f"[Maintenance] Données supprimées: {result}")
            cp.print_info(f"[Maintenance] Stats supprimées: {stats_result}")
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur nettoyage mensuel: {e}")
    
    def run_manual_cleanup_now(self, days_to_keep: int = 90):
        """Exécuter un nettoyage manuel immédiatement"""
        try:
            cp.print_info(f"[Maintenance] Nettoyage manuel immédiat (garder {days_to_keep} jours)...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.run_manual_cleanup(days_to_keep))
            loop.close()
            cp.print_success("[Maintenance] Nettoyage manuel terminé")
            return result
        except Exception as e:
            cp.print_error(f"[Maintenance] Erreur nettoyage manuel: {e}")
            return {"error": str(e)}
    
    def get_next_scheduled_tasks(self):
        """Obtenir les prochaines tâches planifiées"""
        jobs = schedule.get_jobs()
        next_tasks = []
        
        for job in jobs:
            next_run = job.next_run
            if next_run:
                next_tasks.append({
                    "task": str(job.job_func),
                    "next_run": next_run.isoformat(),
                    "interval": str(job.interval)
                })
        
        return next_tasks

# Instance globale unifiée
maintenance_service = AutomatedMaintenanceService()

# Fonctions utilitaires pour l'intégration FastAPI
def start_background_tasks():
    """Démarrer les tâches automatiques au démarrage de l'application"""
    maintenance_service.start_background_service()

def stop_background_tasks():
    """Arrêter les tâches automatiques à l'arrêt de l'application"""
    maintenance_service.stop_background_service()

def manual_cleanup(days_to_keep: int = 90):
    """Interface pour déclencher un nettoyage manuel"""
    return maintenance_service.run_manual_cleanup_now(days_to_keep)

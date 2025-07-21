"""
Gestionnaire de statistiques RAG avancées
"""

from datetime import datetime, timedelta, date
from sqlmodel import Session, select, func, and_, or_
from typing import Dict, Any, List, Optional
from .models import RAGConversation, RAGTokenOperation, RAGContextDocument
from .models import RAGDailyStats, RAGMonthlyStats, RAGYearlyStats
import json
from color_utils import ColorPrint

cp = ColorPrint()

class StatsManager:
    """Gestionnaire central des statistiques RAG"""
    
    async def calculate_daily_stats(self, target_date: date, session: Session) -> Dict[str, Any]:
        """Calculer les statistiques d'une journée spécifique"""
        
        # Début et fin de la journée
        start_date = datetime.combine(target_date, datetime.min.time())
        end_date = datetime.combine(target_date, datetime.max.time())
        
        # Requête de base pour les conversations du jour
        base_query = select(RAGConversation).where(
            and_(
                RAGConversation.timestamp >= start_date,
                RAGConversation.timestamp <= end_date
            )
        )
        
        conversations = session.exec(base_query).all()
        
        if not conversations:
            return self._empty_daily_stats()
        
        # Calculs de base
        total_conversations = len(conversations)
        successful_conversations = sum(1 for c in conversations if c.success)
        failed_conversations = total_conversations - successful_conversations
        
        # Tokens et coûts
        total_tokens = sum(c.grand_total_tokens or 0 for c in conversations)
        total_input_tokens = sum(c.total_input_tokens or 0 for c in conversations)
        total_output_tokens = sum(c.total_output_tokens or 0 for c in conversations)
        total_cost = sum(c.total_cost_usd or 0 for c in conversations)
        
        # Temps de réponse
        response_times = [c.response_time for c in conversations if c.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Analyse des intentions
        intents = {}
        specialities = {}
        
        for conv in conversations:
            if conv.intent_analysis:
                try:
                    intent_data = json.loads(conv.intent_analysis)
                    intent = intent_data.get("intent")
                    speciality = intent_data.get("speciality")
                    
                    if intent:
                        intents[intent] = intents.get(intent, 0) + 1
                    if speciality:
                        specialities[speciality] = specialities.get(speciality, 0) + 1
                except:
                    pass
        
        # Documents contextuels
        total_context_docs = sum(c.context_docs_count or 0 for c in conversations)
        total_sources = sum(c.sources_count or 0 for c in conversations)
        
        return {
            "total_conversations": total_conversations,
            "successful_conversations": successful_conversations,
            "failed_conversations": failed_conversations,
            "success_rate": (successful_conversations / total_conversations * 100) if total_conversations > 0 else 0,
            "total_tokens": total_tokens,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_response_time": round(avg_response_time, 3) if avg_response_time else 0,
            "min_response_time": round(min_response_time, 3) if min_response_time else 0,
            "max_response_time": round(max_response_time, 3) if max_response_time else 0,
            "total_context_docs": total_context_docs,
            "total_sources": total_sources,
            "avg_context_docs_per_conv": round(total_context_docs / total_conversations, 2) if total_conversations > 0 else 0,
            "avg_sources_per_conv": round(total_sources / total_conversations, 2) if total_conversations > 0 else 0,
            "intents_distribution": json.dumps(intents),
            "specialities_distribution": json.dumps(specialities),
            "unique_sessions": len(set(c.session_id for c in conversations))
        }
    
    async def calculate_monthly_stats(self, year: int, month: int, session: Session) -> Dict[str, Any]:
        """Calculer les statistiques d'un mois spécifique"""
        
        # Premier et dernier jour du mois
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Récupérer les stats journalières du mois
        daily_stats = session.exec(
            select(RAGDailyStats).where(
                and_(
                    RAGDailyStats.date >= start_date.date(),
                    RAGDailyStats.date <= end_date.date()
                )
            )
        ).all()
        
        if not daily_stats:
            return self._empty_monthly_stats()
        
        # Agrégation des données journalières
        total_conversations = sum(d.total_conversations for d in daily_stats)
        total_successful = sum(d.successful_conversations for d in daily_stats)
        total_failed = sum(d.failed_conversations for d in daily_stats)
        total_tokens = sum(d.total_tokens for d in daily_stats)
        total_cost = sum(d.total_cost_usd for d in daily_stats)
        
        # Moyennes pondérées
        total_response_times = []
        for d in daily_stats:
            if d.avg_response_time and d.total_conversations > 0:
                total_response_times.extend([d.avg_response_time] * d.total_conversations)
        
        avg_response_time = sum(total_response_times) / len(total_response_times) if total_response_times else 0
        
        # Agrégation des intentions et spécialités
        all_intents = {}
        all_specialities = {}
        
        for d in daily_stats:
            if d.intents_distribution:
                try:
                    intents = json.loads(d.intents_distribution)
                    for intent, count in intents.items():
                        all_intents[intent] = all_intents.get(intent, 0) + count
                except:
                    pass
            
            if d.specialities_distribution:
                try:
                    specialities = json.loads(d.specialities_distribution)
                    for spec, count in specialities.items():
                        all_specialities[spec] = all_specialities.get(spec, 0) + count
                except:
                    pass
        
        return {
            "total_conversations": total_conversations,
            "successful_conversations": total_successful,
            "failed_conversations": total_failed,
            "success_rate": (total_successful / total_conversations * 100) if total_conversations > 0 else 0,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_response_time": round(avg_response_time, 3),
            "intents_distribution": json.dumps(all_intents),
            "specialities_distribution": json.dumps(all_specialities),
            "active_days": len(daily_stats),
            "avg_conversations_per_day": round(total_conversations / len(daily_stats), 2) if daily_stats else 0,
            "peak_day": max(daily_stats, key=lambda x: x.total_conversations).date.isoformat() if daily_stats else None,
            "peak_day_conversations": max(d.total_conversations for d in daily_stats) if daily_stats else 0
        }
    
    async def calculate_yearly_stats(self, year: int, session: Session) -> Dict[str, Any]:
        """Calculer les statistiques d'une année spécifique"""
        
        # Récupérer les stats mensuelles de l'année
        monthly_stats = session.exec(
            select(RAGMonthlyStats).where(RAGMonthlyStats.year == year)
        ).all()
        
        if not monthly_stats:
            return self._empty_yearly_stats()
        
        # Agrégation des données mensuelles
        total_conversations = sum(m.total_conversations for m in monthly_stats)
        total_successful = sum(m.successful_conversations for m in monthly_stats)
        total_failed = sum(m.failed_conversations for m in monthly_stats)
        total_tokens = sum(m.total_tokens for m in monthly_stats)
        total_cost = sum(m.total_cost_usd for m in monthly_stats)
        
        # Moyennes pondérées
        total_response_times = []
        for m in monthly_stats:
            if m.avg_response_time and m.total_conversations > 0:
                total_response_times.extend([m.avg_response_time] * m.total_conversations)
        
        avg_response_time = sum(total_response_times) / len(total_response_times) if total_response_times else 0
        
        # Évolution mensuelle
        monthly_evolution = []
        for m in sorted(monthly_stats, key=lambda x: x.month):
            monthly_evolution.append({
                "month": m.month,
                "conversations": m.total_conversations,
                "cost": m.total_cost_usd,
                "success_rate": m.success_rate
            })
        
        # Agrégation des intentions et spécialités
        all_intents = {}
        all_specialities = {}
        
        for m in monthly_stats:
            if m.intents_distribution:
                try:
                    intents = json.loads(m.intents_distribution)
                    for intent, count in intents.items():
                        all_intents[intent] = all_intents.get(intent, 0) + count
                except:
                    pass
            
            if m.specialities_distribution:
                try:
                    specialities = json.loads(m.specialities_distribution)
                    for spec, count in specialities.items():
                        all_specialities[spec] = all_specialities.get(spec, 0) + count
                except:
                    pass
        
        return {
            "total_conversations": total_conversations,
            "successful_conversations": total_successful,
            "failed_conversations": total_failed,
            "success_rate": (total_successful / total_conversations * 100) if total_conversations > 0 else 0,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_response_time": round(avg_response_time, 3),
            "intents_distribution": json.dumps(all_intents),
            "specialities_distribution": json.dumps(all_specialities),
            "active_months": len(monthly_stats),
            "avg_conversations_per_month": round(total_conversations / len(monthly_stats), 2) if monthly_stats else 0,
            "peak_month": max(monthly_stats, key=lambda x: x.total_conversations).month if monthly_stats else None,
            "peak_month_conversations": max(m.total_conversations for m in monthly_stats) if monthly_stats else 0,
            "monthly_evolution": json.dumps(monthly_evolution)
        }
    
    def _empty_daily_stats(self) -> Dict[str, Any]:
        """Retourner des stats journalières vides"""
        return {
            "total_conversations": 0,
            "successful_conversations": 0,
            "failed_conversations": 0,
            "success_rate": 0,
            "total_tokens": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0,
            "avg_response_time": 0,
            "min_response_time": 0,
            "max_response_time": 0,
            "total_context_docs": 0,
            "total_sources": 0,
            "avg_context_docs_per_conv": 0,
            "avg_sources_per_conv": 0,
            "intents_distribution": "{}",
            "specialities_distribution": "{}",
            "unique_sessions": 0
        }
    
    def _empty_monthly_stats(self) -> Dict[str, Any]:
        """Retourner des stats mensuelles vides"""
        return {
            "total_conversations": 0,
            "successful_conversations": 0,
            "failed_conversations": 0,
            "success_rate": 0,
            "total_tokens": 0,
            "total_cost_usd": 0,
            "avg_response_time": 0,
            "intents_distribution": "{}",
            "specialities_distribution": "{}",
            "active_days": 0,
            "avg_conversations_per_day": 0,
            "peak_day": None,
            "peak_day_conversations": 0
        }
    
    def _empty_yearly_stats(self) -> Dict[str, Any]:
        """Retourner des stats annuelles vides"""
        return {
            "total_conversations": 0,
            "successful_conversations": 0,
            "failed_conversations": 0,
            "success_rate": 0,
            "total_tokens": 0,
            "total_cost_usd": 0,
            "avg_response_time": 0,
            "intents_distribution": "{}",
            "specialities_distribution": "{}",
            "active_months": 0,
            "avg_conversations_per_month": 0,
            "peak_month": None,
            "peak_month_conversations": 0,
            "monthly_evolution": "[]"
        }

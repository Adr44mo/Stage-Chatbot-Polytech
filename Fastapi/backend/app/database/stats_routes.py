"""
Routes API pour les statistiques RAG (journalières, mensuelles, annuelles)
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlmodel import Session, select
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .database import get_session
from .models import RAGDailyStats, RAGMonthlyStats, RAGYearlyStats, RAGConversation
from .stats_manager import StatsManager
from .automated_tasks import AutomatedMaintenanceService
from pydantic import BaseModel
import json
from color_utils import ColorPrint

cp = ColorPrint()

router = APIRouter(prefix="/intelligent-rag/stats", tags=["Statistics RAG"])

# Instance globale du service de maintenance
maintenance_service = AutomatedMaintenanceService()

# ================================
# MODÈLES PYDANTIC
# ================================

class DailyStatsResponse(BaseModel):
    date: str
    total_conversations: int
    successful_conversations: int
    failed_conversations: int
    success_rate: float
    total_tokens: int
    total_cost_usd: float
    avg_response_time: float
    intents_distribution: Dict[str, int]
    specialities_distribution: Dict[str, int]

class MonthlyStatsResponse(BaseModel):
    year: int
    month: int
    total_conversations: int
    successful_conversations: int
    failed_conversations: int
    success_rate: float
    total_tokens: int
    total_cost_usd: float
    avg_response_time: float
    active_days: int
    peak_day: Optional[str]
    peak_day_conversations: int

class YearlyStatsResponse(BaseModel):
    year: int
    total_conversations: int
    successful_conversations: int
    failed_conversations: int
    success_rate: float
    total_tokens: int
    total_cost_usd: float
    avg_response_time: float
    active_months: int
    peak_month: Optional[int]
    peak_month_conversations: int
    monthly_evolution: List[Dict[str, Any]]

# ================================
# ROUTES STATISTIQUES JOURNALIÈRES
# ================================

@router.get("/daily", response_model=List[DailyStatsResponse])
async def get_daily_stats(
    limit: int = Query(30, description="Nombre de jours à récupérer"),
    session: Session = Depends(get_session)
):
    """Récupérer les statistiques journalières récentes"""
    try:
        daily_stats = session.exec(
            select(RAGDailyStats)
            .order_by(RAGDailyStats.date.desc())
            .limit(limit)
        ).all()
        
        result = []
        for stat in daily_stats:
            intents = json.loads(stat.intents_distribution) if stat.intents_distribution else {}
            specialities = json.loads(stat.specialities_distribution) if stat.specialities_distribution else {}
            
            result.append(DailyStatsResponse(
                date=stat.date.isoformat(),
                total_conversations=stat.total_conversations,
                successful_conversations=stat.successful_conversations,
                failed_conversations=stat.failed_conversations,
                success_rate=stat.success_rate,
                total_tokens=stat.total_tokens,
                total_cost_usd=stat.total_cost_usd,
                avg_response_time=stat.avg_response_time,
                intents_distribution=intents,
                specialities_distribution=specialities
            ))
        
        return result
        
    except Exception as e:
        cp.print_error(f"Erreur récupération stats journalières: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{target_date}")
async def get_daily_stats_for_date(
    target_date: str = Path(..., description="Date au format YYYY-MM-DD"),
    session: Session = Depends(get_session)
):
    """Récupérer les statistiques d'une date spécifique"""
    try:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        
        daily_stat = session.exec(
            select(RAGDailyStats).where(RAGDailyStats.date == date_obj)
        ).first()
        
        if not daily_stat:
            # Calculer les stats à la volée si elles n'existent pas
            stats_manager = StatsManager()
            stats_data = await stats_manager.calculate_daily_stats(date_obj, session)
            
            return {
                "date": target_date,
                **stats_data,
                "note": "Statistiques calculées à la volée (non mises en cache)"
            }
        
        intents = json.loads(daily_stat.intents_distribution) if daily_stat.intents_distribution else {}
        specialities = json.loads(daily_stat.specialities_distribution) if daily_stat.specialities_distribution else {}
        
        return DailyStatsResponse(
            date=daily_stat.date.isoformat(),
            total_conversations=daily_stat.total_conversations,
            successful_conversations=daily_stat.successful_conversations,
            failed_conversations=daily_stat.failed_conversations,
            success_rate=daily_stat.success_rate,
            total_tokens=daily_stat.total_tokens,
            total_cost_usd=daily_stat.total_cost_usd,
            avg_response_time=daily_stat.avg_response_time,
            intents_distribution=intents,
            specialities_distribution=specialities
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")
    except Exception as e:
        cp.print_error(f"Erreur récupération stats pour {target_date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ROUTES STATISTIQUES MENSUELLES
# ================================

@router.get("/monthly", response_model=List[MonthlyStatsResponse])
async def get_monthly_stats(
    limit: int = Query(12, description="Nombre de mois à récupérer"),
    session: Session = Depends(get_session)
):
    """Récupérer les statistiques mensuelles récentes"""
    try:
        monthly_stats = session.exec(
            select(RAGMonthlyStats)
            .order_by(RAGMonthlyStats.year.desc(), RAGMonthlyStats.month.desc())
            .limit(limit)
        ).all()
        
        result = []
        for stat in monthly_stats:
            result.append(MonthlyStatsResponse(
                year=stat.year,
                month=stat.month,
                total_conversations=stat.total_conversations,
                successful_conversations=stat.successful_conversations,
                failed_conversations=stat.failed_conversations,
                success_rate=stat.success_rate,
                total_tokens=stat.total_tokens,
                total_cost_usd=stat.total_cost_usd,
                avg_response_time=stat.avg_response_time,
                active_days=stat.active_days,
                peak_day=stat.peak_day,
                peak_day_conversations=stat.peak_day_conversations
            ))
        
        return result
        
    except Exception as e:
        cp.print_error(f"Erreur récupération stats mensuelles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monthly/{year}/{month}")
async def get_monthly_stats_for_period(
    year: int = Path(..., description="Année"),
    month: int = Path(..., ge=1, le=12, description="Mois (1-12)"),
    session: Session = Depends(get_session)
):
    """Récupérer les statistiques d'un mois spécifique"""
    try:
        monthly_stat = session.exec(
            select(RAGMonthlyStats).where(
                RAGMonthlyStats.year == year,
                RAGMonthlyStats.month == month
            )
        ).first()
        
        if not monthly_stat:
            # Calculer les stats à la volée
            stats_manager = StatsManager()
            stats_data = await stats_manager.calculate_monthly_stats(year, month, session)
            
            return {
                "year": year,
                "month": month,
                **stats_data,
                "note": "Statistiques calculées à la volée (non mises en cache)"
            }
        
        return MonthlyStatsResponse(
            year=monthly_stat.year,
            month=monthly_stat.month,
            total_conversations=monthly_stat.total_conversations,
            successful_conversations=monthly_stat.successful_conversations,
            failed_conversations=monthly_stat.failed_conversations,
            success_rate=monthly_stat.success_rate,
            total_tokens=monthly_stat.total_tokens,
            total_cost_usd=monthly_stat.total_cost_usd,
            avg_response_time=monthly_stat.avg_response_time,
            active_days=monthly_stat.active_days,
            peak_day=monthly_stat.peak_day,
            peak_day_conversations=monthly_stat.peak_day_conversations
        )
        
    except Exception as e:
        cp.print_error(f"Erreur récupération stats pour {month}/{year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ROUTES STATISTIQUES ANNUELLES
# ================================

@router.get("/yearly", response_model=List[YearlyStatsResponse])
async def get_yearly_stats(
    limit: int = Query(5, description="Nombre d'années à récupérer"),
    session: Session = Depends(get_session)
):
    """Récupérer les statistiques annuelles récentes"""
    try:
        yearly_stats = session.exec(
            select(RAGYearlyStats)
            .order_by(RAGYearlyStats.year.desc())
            .limit(limit)
        ).all()
        
        result = []
        for stat in yearly_stats:
            monthly_evolution = json.loads(stat.monthly_evolution) if stat.monthly_evolution else []
            
            result.append(YearlyStatsResponse(
                year=stat.year,
                total_conversations=stat.total_conversations,
                successful_conversations=stat.successful_conversations,
                failed_conversations=stat.failed_conversations,
                success_rate=stat.success_rate,
                total_tokens=stat.total_tokens,
                total_cost_usd=stat.total_cost_usd,
                avg_response_time=stat.avg_response_time,
                active_months=stat.active_months,
                peak_month=stat.peak_month,
                peak_month_conversations=stat.peak_month_conversations,
                monthly_evolution=monthly_evolution
            ))
        
        return result
        
    except Exception as e:
        cp.print_error(f"Erreur récupération stats annuelles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/yearly/{year}")
async def get_yearly_stats_for_year(
    year: int = Path(..., description="Année"),
    session: Session = Depends(get_session)
):
    """Récupérer les statistiques d'une année spécifique"""
    try:
        yearly_stat = session.exec(
            select(RAGYearlyStats).where(RAGYearlyStats.year == year)
        ).first()
        
        if not yearly_stat:
            # Calculer les stats à la volée
            stats_manager = StatsManager()
            stats_data = await stats_manager.calculate_yearly_stats(year, session)
            
            return {
                "year": year,
                **stats_data,
                "note": "Statistiques calculées à la volée (non mises en cache)"
            }
        
        monthly_evolution = json.loads(yearly_stat.monthly_evolution) if yearly_stat.monthly_evolution else []
        
        return YearlyStatsResponse(
            year=yearly_stat.year,
            total_conversations=yearly_stat.total_conversations,
            successful_conversations=yearly_stat.successful_conversations,
            failed_conversations=yearly_stat.failed_conversations,
            success_rate=yearly_stat.success_rate,
            total_tokens=yearly_stat.total_tokens,
            total_cost_usd=yearly_stat.total_cost_usd,
            avg_response_time=yearly_stat.avg_response_time,
            active_months=yearly_stat.active_months,
            peak_month=yearly_stat.peak_month,
            peak_month_conversations=yearly_stat.peak_month_conversations,
            monthly_evolution=monthly_evolution
        )
        
    except Exception as e:
        cp.print_error(f"Erreur récupération stats pour {year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ROUTES DE MAINTENANCE
# ================================

@router.post("/update/daily/{target_date}")
async def update_daily_stats(
    target_date: str = Path(..., description="Date au format YYYY-MM-DD"),
):
    """Forcer la mise à jour des statistiques journalières"""
    try:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        await maintenance_service.update_daily_stats(date_obj)
        
        return {
            "message": f"Statistiques journalières mises à jour pour {target_date}",
            "date": target_date
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD")
    except Exception as e:
        cp.print_error(f"Erreur mise à jour stats journalières: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update/monthly/{year}/{month}")
async def update_monthly_stats(
    year: int = Path(..., description="Année"),
    month: int = Path(..., ge=1, le=12, description="Mois (1-12)"),
):
    """Forcer la mise à jour des statistiques mensuelles"""
    try:
        await maintenance_service.update_monthly_stats(year, month)
        
        return {
            "message": f"Statistiques mensuelles mises à jour pour {month}/{year}",
            "year": year,
            "month": month
        }
        
    except Exception as e:
        cp.print_error(f"Erreur mise à jour stats mensuelles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update/yearly/{year}")
async def update_yearly_stats(
    year: int = Path(..., description="Année"),
):
    """Forcer la mise à jour des statistiques annuelles"""
    try:
        await maintenance_service.update_yearly_stats(year)
        
        return {
            "message": f"Statistiques annuelles mises à jour pour {year}",
            "year": year
        }
        
    except Exception as e:
        cp.print_error(f"Erreur mise à jour stats annuelles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance/run")
async def run_maintenance():
    """Lancer la maintenance automatisée"""
    try:
        await maintenance_service.run_daily_maintenance()
        
        return {
            "message": "Maintenance automatisée terminée avec succès",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        cp.print_error(f"Erreur maintenance automatisée: {e}")
        raise HTTPException(status_code=500, detail=str(e))
